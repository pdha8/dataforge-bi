"""
apps/ml_analytics/ml/forecasting.py

Service de prévision de séries temporelles.
Supporte : Prophet, ARIMA, SARIMA, XGBoost.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses résultat
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ForecastPoint:
    date: str
    value: float
    lower_bound: float
    upper_bound: float

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "value": round(self.value, 4),
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
        }


@dataclass
class EvaluationMetrics:
    mape: float
    rmse: float
    mae: float
    accuracy: float

    def to_dict(self) -> dict:
        return {
            "mape": round(self.mape, 4),
            "rmse": round(self.rmse, 4),
            "mae": round(self.mae, 4),
            "accuracy": round(self.accuracy, 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class ForecastingError(Exception):
    """Erreur de base pour le service de prévision."""


class ModelNotFittedError(ForecastingError):
    """Le modèle n'a pas été entraîné."""


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class ForecastingService:
    """
    Service de prévision de séries temporelles.

    data attendu : [{"date": "YYYY-MM-DD", "value": float}, ...]
    """

    def __init__(self, model_instance):
        self.model = model_instance
        self.config: dict = model_instance.config
        self.params: dict = model_instance.parameters
        self._fitted_model: Any = None
        self._last_date: Optional[pd.Timestamp] = None
        self._history: Optional[pd.Series] = None

    # ── Propriété ────────────────────────────────────────────────────────────

    @property
    def is_fitted(self) -> bool:
        return self._fitted_model is not None

    # ── Entraînement ─────────────────────────────────────────────────────────

    def train(self, data: list[dict]) -> None:
        """Entraîne le modèle selon l'algorithme configuré."""
        if not data:
            raise ForecastingError("Le dataset d'entraînement est vide.")
        algo = self.model.algorithm
        dispatch = {
            "prophet":  self._train_prophet,
            "arima":    self._train_arima,
            "sarima":   self._train_sarima,
            "xgboost":  self._train_xgboost,
        }
        trainer = dispatch.get(algo)
        if trainer is None:
            raise ForecastingError(f"Algorithme de prévision non supporté : '{algo}'.")
        trainer(data)
        self._last_date = pd.to_datetime(max(item["date"] for item in data))
        self._history = pd.Series(
            [float(item["value"]) for item in data],
            index=pd.to_datetime([item["date"] for item in data]),
        )
        logger.info(
            "ForecastingService trained: algo=%s, n=%d, last_date=%s",
            algo, len(data), self._last_date.date(),
        )

    def _train_prophet(self, data: list[dict]) -> None:
        try:
            from prophet import Prophet
        except ImportError:
            raise ForecastingError(
                "Prophet non installé. Exécutez : pip install prophet"
            )
        df = pd.DataFrame({
            "ds": pd.to_datetime([item["date"] for item in data]),
            "y": [float(item["value"]) for item in data],
        })
        m = Prophet(
            yearly_seasonality=self.config.get("yearly_seasonality", True),
            weekly_seasonality=self.config.get("weekly_seasonality", True),
            daily_seasonality=self.config.get("daily_seasonality", False),
            changepoint_prior_scale=self.config.get("changepoint_prior_scale", 0.05),
            seasonality_prior_scale=self.config.get("seasonality_prior_scale", 10.0),
            seasonality_mode=self.config.get("seasonality_mode", "additive"),
        )
        for s in self.config.get("custom_seasonalities", []):
            m.add_seasonality(
                name=s["name"],
                period=s["period"],
                fourier_order=s.get("fourier_order", 5),
            )
        if holidays := self.config.get("holidays"):
            m.add_country_holidays(country_name=holidays)
        m.fit(df)
        self._fitted_model = m

    def _train_arima(self, data: list[dict]) -> None:
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            raise ForecastingError("statsmodels non installé. Exécutez : pip install statsmodels")
        series = pd.Series([float(item["value"]) for item in data])
        order = (
            self.params.get("p", 5),
            self.params.get("d", 1),
            self.params.get("q", 0),
        )
        self._fitted_model = ARIMA(series, order=order).fit()

    def _train_sarima(self, data: list[dict]) -> None:
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
        except ImportError:
            raise ForecastingError("statsmodels non installé.")
        series = pd.Series([float(item["value"]) for item in data])
        order = (self.params.get("p", 1), self.params.get("d", 1), self.params.get("q", 1))
        seasonal_order = (
            self.params.get("P", 0), self.params.get("D", 1),
            self.params.get("Q", 0), self.params.get("s", 12),
        )
        self._fitted_model = SARIMAX(series, order=order, seasonal_order=seasonal_order).fit(disp=False)

    def _train_xgboost(self, data: list[dict]) -> None:
        try:
            import xgboost as xgb
        except ImportError:
            raise ForecastingError("xgboost non installé. Exécutez : pip install xgboost")
        df = self._build_xgb_features(pd.DataFrame(data))
        df = df.dropna()
        if df.empty:
            raise ForecastingError("Données insuffisantes pour XGBoost après création des features.")
        feature_cols = [c for c in df.columns if c not in ("date", "value")]
        X, y = df[feature_cols].values, df["value"].values
        self._fitted_model = xgb.XGBRegressor(
            n_estimators=self.params.get("n_estimators", 200),
            max_depth=self.params.get("max_depth", 6),
            learning_rate=self.params.get("learning_rate", 0.05),
            subsample=self.params.get("subsample", 0.8),
            colsample_bytree=self.params.get("colsample_bytree", 0.8),
            random_state=42,
            n_jobs=-1,
        )
        self._fitted_model.fit(X, y)
        self._xgb_feature_cols = feature_cols

    @staticmethod
    def _build_xgb_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = df["value"].astype(float)
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["dayofweek"] = df["date"].dt.dayofweek
        df["quarter"] = df["date"].dt.quarter
        for lag in [1, 2, 3, 7, 14, 30]:
            df[f"lag_{lag}"] = df["value"].shift(lag)
        for window in [7, 14, 30]:
            df[f"roll_mean_{window}"] = df["value"].rolling(window).mean()
            df[f"roll_std_{window}"] = df["value"].rolling(window).std()
        return df

    # ── Prévision ────────────────────────────────────────────────────────────

    def forecast(self, horizon: int) -> list[dict]:
        """Génère `horizon` points de prévision après la dernière date d'entraînement."""
        self._assert_fitted()
        algo = self.model.algorithm
        dispatch = {
            "prophet": self._forecast_prophet,
            "arima":   self._forecast_arima,
            "sarima":  self._forecast_sarima,
            "xgboost": self._forecast_xgboost,
        }
        points = dispatch[algo](horizon)
        return [p.to_dict() for p in points]

    def _forecast_prophet(self, horizon: int) -> list[ForecastPoint]:
        future = self._fitted_model.make_future_dataframe(periods=horizon)
        pred = self._fitted_model.predict(future).tail(horizon)
        return [
            ForecastPoint(
                date=row["ds"].isoformat()[:10],
                value=float(row["yhat"]),
                lower_bound=float(row["yhat_lower"]),
                upper_bound=float(row["yhat_upper"]),
            )
            for _, row in pred.iterrows()
        ]

    def _forecast_arima(self, horizon: int) -> list[ForecastPoint]:
        fc = self._fitted_model.get_forecast(steps=horizon)
        means = fc.predicted_mean
        ci = fc.conf_int()
        points = []
        for i in range(horizon):
            date = (self._last_date + timedelta(days=i + 1)).isoformat()[:10]
            points.append(ForecastPoint(
                date=date,
                value=float(means.iloc[i]),
                lower_bound=float(ci.iloc[i, 0]),
                upper_bound=float(ci.iloc[i, 1]),
            ))
        return points

    def _forecast_sarima(self, horizon: int) -> list[ForecastPoint]:
        return self._forecast_arima(horizon)

    def _forecast_xgboost(self, horizon: int) -> list[ForecastPoint]:
        """Prévision itérative XGBoost (1 step ahead répété)."""
        history = self._history.copy()
        points = []
        for i in range(horizon):
            next_date = self._last_date + timedelta(days=i + 1)
            row = pd.DataFrame([{
                "date": next_date.isoformat()[:10],
                "value": history.iloc[-1],
            }])
            row = self._build_xgb_features(row)
            for col in self._xgb_feature_cols:
                if col not in row.columns:
                    row[col] = 0.0
            X = row[self._xgb_feature_cols].fillna(0).values
            pred_val = float(self._fitted_model.predict(X)[0])
            std = float(history.std()) if len(history) > 1 else 0.0
            points.append(ForecastPoint(
                date=next_date.isoformat()[:10],
                value=pred_val,
                lower_bound=pred_val - 1.96 * std,
                upper_bound=pred_val + 1.96 * std,
            ))
            history.loc[next_date] = pred_val
        return points

    # ── Prédiction ponctuelle ─────────────────────────────────────────────────

    def predict(self, data: list[dict]) -> list[float]:
        """Prédit les valeurs pour les dates fournies (in-sample)."""
        self._assert_fitted()
        algo = self.model.algorithm
        if algo == "prophet":
            df = pd.DataFrame({"ds": pd.to_datetime([item["date"] for item in data])})
            return self._fitted_model.predict(df)["yhat"].tolist()
        if algo in ("arima", "sarima"):
            return self._fitted_model.forecast(steps=len(data)).tolist()
        if algo == "xgboost":
            df = self._build_xgb_features(pd.DataFrame(data))
            for col in self._xgb_feature_cols:
                if col not in df.columns:
                    df[col] = 0.0
            X = df[self._xgb_feature_cols].fillna(0).values
            return self._fitted_model.predict(X).tolist()
        return []

    # ── Évaluation ────────────────────────────────────────────────────────────

    def evaluate(self, test_data: list[dict]) -> dict:
        """Évalue les performances sur un jeu de test."""
        self._assert_fitted()
        y_true = [float(item["value"]) for item in test_data]
        y_pred = self.predict(test_data)
        if not y_pred or len(y_pred) != len(y_true):
            return {"error": "Prédictions invalides."}
        y_true_arr, y_pred_arr = np.array(y_true), np.array(y_pred)
        mape = float(mean_absolute_percentage_error(y_true_arr, y_pred_arr)) * 100
        rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr)))
        mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
        return EvaluationMetrics(
            mape=mape, rmse=rmse, mae=mae, accuracy=max(0.0, 100.0 - mape)
        ).to_dict()

    # ── Persistance ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        self._assert_fitted()
        joblib.dump({
            "fitted_model": self._fitted_model,
            "last_date": self._last_date,
            "history": self._history,
            "algorithm": self.model.algorithm,
            "xgb_feature_cols": getattr(self, "_xgb_feature_cols", []),
        }, path, compress=3)
        logger.info("ForecastingService saved: path=%s", path)

    def load(self, path: str) -> None:
        payload = joblib.load(path)
        self._fitted_model = payload["fitted_model"]
        self._last_date = payload["last_date"]
        self._history = payload["history"]
        self._xgb_feature_cols = payload.get("xgb_feature_cols", [])

    # ── Privé ─────────────────────────────────────────────────────────────────

    def _assert_fitted(self) -> None:
        if not self.is_fitted:
            raise ModelNotFittedError("Le modèle n'a pas encore été entraîné.")
