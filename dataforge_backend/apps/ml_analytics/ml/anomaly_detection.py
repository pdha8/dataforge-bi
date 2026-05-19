"""
apps/ml_analytics/ml/anomaly_detection.py

Service de détection d'anomalies.
Supporte : Isolation Forest, Elliptic Envelope, One-Class SVM.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DetectedAnomaly:
    index: int
    date: str
    value: float
    expected: float
    score: float
    severity: str

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "date": self.date,
            "value": round(self.value, 4),
            "expected": round(self.expected, 4),
            "score": round(self.score, 6),
            "severity": self.severity,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class AnomalyDetectionError(Exception):
    """Erreur de base pour le service de détection d'anomalies."""


class DetectorNotFittedError(AnomalyDetectionError):
    """Le détecteur n'a pas encore été entraîné."""


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class AnomalyDetectionService:
    """
    Service de détection d'anomalies non supervisée.

    data attendu : [{"date": "YYYY-MM-DD", "value": float}, ...]
    """

    def __init__(self, model_instance):
        self.model = model_instance
        self.config: dict = model_instance.config
        self.params: dict = model_instance.parameters
        self._detector: Optional[Any] = None
        self._scaler: Optional[StandardScaler] = None

    @property
    def is_fitted(self) -> bool:
        return self._detector is not None and self._scaler is not None

    # ── Entraînement ─────────────────────────────────────────────────────────

    def train(self, data: list[dict]) -> None:
        if not data:
            raise AnomalyDetectionError("Le dataset d'entraînement est vide.")
        algo = self.model.algorithm
        dispatch = {
            "isolation_forest":  self._train_isolation_forest,
            "elliptic_envelope": self._train_elliptic_envelope,
            "svm":               self._train_one_class_svm,
        }
        trainer = dispatch.get(algo)
        if trainer is None:
            raise AnomalyDetectionError(
                f"Algorithme de détection d'anomalies non supporté : '{algo}'."
            )
        trainer(data)
        logger.info(
            "AnomalyDetectionService trained: algo=%s, n=%d", algo, len(data)
        )

    def _train_isolation_forest(self, data: list[dict]) -> None:
        features = self._build_features(data)
        self._scaler = StandardScaler()
        X = self._scaler.fit_transform(features)
        self._detector = IsolationForest(
            contamination=self.params.get("contamination", 0.05),
            n_estimators=self.params.get("n_estimators", 200),
            max_samples=self.params.get("max_samples", "auto"),
            random_state=42,
            n_jobs=-1,
        )
        self._detector.fit(X)

    def _train_elliptic_envelope(self, data: list[dict]) -> None:
        features = self._build_features(data)
        self._scaler = StandardScaler()
        X = self._scaler.fit_transform(features)
        self._detector = EllipticEnvelope(
            contamination=self.params.get("contamination", 0.05),
            random_state=42,
        )
        self._detector.fit(X)

    def _train_one_class_svm(self, data: list[dict]) -> None:
        features = self._build_features(data)
        self._scaler = StandardScaler()
        X = self._scaler.fit_transform(features)
        self._detector = OneClassSVM(
            nu=self.params.get("nu", 0.05),
            gamma=self.params.get("gamma", "scale"),
            kernel=self.params.get("kernel", "rbf"),
        )
        self._detector.fit(X)

    # ── Détection ────────────────────────────────────────────────────────────

    def detect(self, data: list[dict]) -> list[dict]:
        """Détecte les anomalies dans les données fournies."""
        self._assert_fitted()
        if not data:
            return []
        features = self._build_features(data)
        X = self._scaler.transform(features)

        predictions = self._detector.predict(X)
        if isinstance(self._detector, IsolationForest):
            scores = self._detector.score_samples(X)
        else:
            scores = -self._detector.decision_function(X)

        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                expected = self._compute_expected(data, i)
                anomalies.append(DetectedAnomaly(
                    index=i,
                    date=str(data[i]["date"]),
                    value=float(data[i]["value"]),
                    expected=expected,
                    score=float(score),
                    severity=self._severity(score),
                ).to_dict())

        logger.info("Anomaly detection: %d/%d points flagged.", len(anomalies), len(data))
        return anomalies

    # ── Évaluation ────────────────────────────────────────────────────────────

    def evaluate(self, test_data: list[dict], labels: Optional[list[int]] = None) -> dict:
        """
        Évalue les performances si les labels vrais sont fournis (1 = anomalie).
        Sans labels, retourne uniquement le nombre d'anomalies trouvées.
        """
        anomalies = self.detect(test_data)
        if labels is None:
            return {"anomalies_found": len(anomalies)}

        predicted_indices = {a["index"] for a in anomalies}
        true_positive_indices = {i for i, l in enumerate(labels) if l == 1}

        tp = len(predicted_indices & true_positive_indices)
        fp = len(predicted_indices - true_positive_indices)
        fn = len(true_positive_indices - predicted_indices)

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "anomalies_found": len(anomalies),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
        }

    # ── Persistance ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        self._assert_fitted()
        joblib.dump({"detector": self._detector, "scaler": self._scaler}, path, compress=3)
        logger.info("AnomalyDetectionService saved: path=%s", path)

    def load(self, path: str) -> None:
        payload = joblib.load(path)
        self._detector = payload["detector"]
        self._scaler = payload["scaler"]

    # ── Méthodes privées ──────────────────────────────────────────────────────

    @staticmethod
    def _build_features(data: list[dict]) -> np.ndarray:
        """
        Construit une matrice de features à partir des données brutes.
        Features : valeur, statistiques glissantes, tendance, jour de la semaine, mois.
        """
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = df["value"].astype(float)
        rows = []
        for i in range(len(df)):
            row = [df.iloc[i]["value"]]
            for w in [3, 7, 14, 30]:
                start = max(0, i - w + 1)
                window = df.iloc[start : i + 1]["value"]
                row.append(float(window.mean()))
                row.append(float(window.std()) if len(window) > 1 else 0.0)
            # Tendance instantanée
            if i >= 1:
                prev = df.iloc[i - 1]["value"]
                trend = (df.iloc[i]["value"] - prev) / (abs(prev) + 1e-10)
            else:
                trend = 0.0
            row.append(trend)
            row.append(int(df.iloc[i]["date"].dayofweek))
            row.append(int(df.iloc[i]["date"].month))
            rows.append(row)
        return np.array(rows, dtype=float)

    @staticmethod
    def _compute_expected(data: list[dict], index: int, window: int = 7) -> float:
        """Calcule la valeur attendue comme moyenne glissante des `window` précédents."""
        start = max(0, index - window)
        values = [float(d["value"]) for d in data[start:index]]
        return float(np.mean(values)) if values else float(data[index]["value"])

    @staticmethod
    def _severity(score: float) -> str:
        """Traduit un score d'anomalie en niveau de sévérité."""
        if score < -0.5:
            return "critical"
        if score < -0.3:
            return "high"
        if score < -0.15:
            return "medium"
        return "low"

    def _assert_fitted(self) -> None:
        if not self.is_fitted:
            raise DetectorNotFittedError("Le détecteur n'a pas encore été entraîné.")
