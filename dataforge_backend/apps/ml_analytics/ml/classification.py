"""
apps/ml_analytics/ml/classification.py

Service de classification ML pour la plateforme Sotifibre BI.
Supporte : Random Forest, XGBoost, Gradient Boosting, SVM,
           Régression Logistique, Réseau de Neurones.

Fonctionnalités :
- Pipeline sklearn (StandardScaler + classifieur) en une seule étape
- Validation croisée stratifiée k-fold intégrée à l'entraînement
- Évaluation complète : accuracy, precision, recall, F1, ROC-AUC,
  matrice de confusion, classification_report
- Importances des features (Random Forest, XGBoost, Logistic Regression)
- Gestion défensive des features manquantes / supplémentaires
- Persistance joblib compressée avec versioning
- Type hints complets et logging structuré
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED_ALGORITHMS = frozenset({
    "random_forest", "xgboost", "gradient_boosting",
    "svm", "logistic_regression", "neural_network",
})
DEFAULT_CV_FOLDS = 5
DEFAULT_RANDOM_STATE = 42
FILL_MISSING_DEFAULT = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses résultat
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TrainingResult:
    algorithm: str
    feature_cols: list[str]
    classes: list[Any]
    n_samples: int
    duration_ms: float
    cv_scores: dict[str, list[float]] = field(default_factory=dict)

    @property
    def cv_accuracy_mean(self) -> Optional[float]:
        scores = self.cv_scores.get("test_accuracy")
        return float(np.mean(scores)) if scores else None

    @property
    def cv_accuracy_std(self) -> Optional[float]:
        scores = self.cv_scores.get("test_accuracy")
        return float(np.std(scores)) if scores else None

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "n_samples": self.n_samples,
            "n_features": len(self.feature_cols),
            "n_classes": len(self.classes),
            "duration_ms": round(self.duration_ms, 2),
            "cv_accuracy_mean": round(self.cv_accuracy_mean, 4) if self.cv_accuracy_mean else None,
            "cv_accuracy_std": round(self.cv_accuracy_std, 4) if self.cv_accuracy_std else None,
        }


@dataclass
class EvaluationResult:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float]
    confusion_matrix: list[list[int]]
    classification_report: str
    n_samples: int

    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 6),
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1_score": round(self.f1_score, 6),
            "roc_auc": round(self.roc_auc, 6) if self.roc_auc is not None else None,
            "confusion_matrix": self.confusion_matrix,
            "classification_report": self.classification_report,
            "n_samples": self.n_samples,
        }


@dataclass
class PredictionResult:
    classes: list[Any]
    probabilities: Optional[list[list[float]]]
    confidence: list[float]

    def to_dict(self) -> dict:
        return {
            "classes": self.classes,
            "probabilities": self.probabilities,
            "confidence": [round(c, 4) for c in self.confidence],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class ClassificationError(Exception):
    """Erreur de base pour le service de classification."""


class ModelNotTrainedError(ClassificationError):
    """Le modèle n'a pas encore été entraîné."""


class UnsupportedAlgorithmError(ClassificationError):
    """Algorithme non supporté."""


class FeatureMismatchError(ClassificationError):
    """Features d'entrée incompatibles avec les features d'entraînement."""


# ─────────────────────────────────────────────────────────────────────────────
# Fabrique de classifieurs
# ─────────────────────────────────────────────────────────────────────────────

def _build_classifier(algorithm: str, params: dict) -> Any:
    """
    Instancie le classifieur approprié selon l'algorithme.
    Si XGBoost n'est pas installé, bascule sur GradientBoosting avec warning.
    """
    rs = DEFAULT_RANDOM_STATE

    if algorithm == "random_forest":
        return RandomForestClassifier(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth", None),
            min_samples_split=params.get("min_samples_split", 2),
            min_samples_leaf=params.get("min_samples_leaf", 1),
            class_weight=params.get("class_weight", "balanced"),
            n_jobs=params.get("n_jobs", -1),
            random_state=rs,
        )

    if algorithm == "xgboost":
        try:
            import xgboost as xgb
            return xgb.XGBClassifier(
                n_estimators=params.get("n_estimators", 200),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.05),
                subsample=params.get("subsample", 0.8),
                colsample_bytree=params.get("colsample_bytree", 0.8),
                use_label_encoder=False,
                eval_metric="mlogloss",
                n_jobs=params.get("n_jobs", -1),
                random_state=rs,
            )
        except ImportError:
            logger.warning(
                "XGBoost non installé — bascule sur GradientBoosting. "
                "Installez-le : pip install xgboost"
            )
            return _build_classifier("gradient_boosting", params)

    if algorithm == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=params.get("n_estimators", 200),
            max_depth=params.get("max_depth", 5),
            learning_rate=params.get("learning_rate", 0.05),
            subsample=params.get("subsample", 0.8),
            random_state=rs,
        )

    if algorithm == "svm":
        return SVC(
            C=params.get("C", 1.0),
            kernel=params.get("kernel", "rbf"),
            gamma=params.get("gamma", "scale"),
            class_weight=params.get("class_weight", "balanced"),
            probability=True,
            random_state=rs,
        )

    if algorithm == "logistic_regression":
        return LogisticRegression(
            C=params.get("C", 1.0),
            solver=params.get("solver", "lbfgs"),
            max_iter=params.get("max_iter", 1000),
            class_weight=params.get("class_weight", "balanced"),
            multi_class="auto",
            n_jobs=params.get("n_jobs", -1),
            random_state=rs,
        )

    if algorithm == "neural_network":
        return MLPClassifier(
            hidden_layer_sizes=tuple(params.get("hidden_layer_sizes", [128, 64])),
            activation=params.get("activation", "relu"),
            solver=params.get("solver", "adam"),
            alpha=params.get("alpha", 1e-4),
            batch_size=params.get("batch_size", "auto"),
            learning_rate_init=params.get("learning_rate_init", 1e-3),
            max_iter=params.get("max_iter", 300),
            early_stopping=params.get("early_stopping", True),
            validation_fraction=params.get("validation_fraction", 0.1),
            random_state=rs,
        )

    raise UnsupportedAlgorithmError(
        f"Algorithme '{algorithm}' non supporté. "
        f"Disponibles : {sorted(SUPPORTED_ALGORITHMS)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Service principal
# ─────────────────────────────────────────────────────────────────────────────

class ClassificationService:
    """
    Service de classification ML.

    Pipeline : StandardScaler → Classifieur sklearn/XGBoost.

    Usage :
        svc = ClassificationService(model_instance)
        result = svc.train(data, target_col="label")
        preds  = svc.predict(new_data)
        eval_  = svc.evaluate(test_data, target_col="label")
        svc.save("/path/to/model.joblib")
    """

    def __init__(self, model_instance) -> None:
        self.model = model_instance
        self.config: dict = model_instance.config
        self.params: dict = model_instance.parameters

        self._pipeline: Optional[Pipeline] = None
        self._label_encoder: Optional[LabelEncoder] = None
        self._feature_cols: list[str] = []
        self._training_result: Optional[TrainingResult] = None

    # ── Propriétés ───────────────────────────────────────────────────────────

    @property
    def is_trained(self) -> bool:
        return self._pipeline is not None and bool(self._feature_cols)

    @property
    def classes_(self) -> list[Any]:
        return list(self._label_encoder.classes_) if self._label_encoder else []

    @property
    def n_features(self) -> int:
        return len(self._feature_cols)

    @property
    def algorithm(self) -> str:
        return self.model.algorithm

    # ── Entraînement ─────────────────────────────────────────────────────────

    def train(
        self,
        data: list[dict],
        target_col: str = "target",
        cross_validate_model: bool = True,
        n_cv_folds: int = DEFAULT_CV_FOLDS,
    ) -> TrainingResult:
        """
        Entraîne le classifieur sur les données fournies.

        Args:
            data                 : Liste de dicts (features + target).
            target_col           : Nom de la colonne cible.
            cross_validate_model : Si True, effectue une validation croisée.
            n_cv_folds           : Nombre de folds CV.

        Returns:
            TrainingResult avec métadonnées d'entraînement.
        """
        if not data:
            raise ValueError("Le dataset d'entraînement est vide.")

        df = self._to_df(data)
        self._check_target(df, target_col)

        feature_cols = [c for c in df.columns if c != target_col]
        if not feature_cols:
            raise ValueError("Aucune feature disponible après exclusion de la cible.")

        X = df[feature_cols].values.astype(float)
        y_raw = df[target_col].values

        self._label_encoder = LabelEncoder()
        y = self._label_encoder.fit_transform(y_raw)

        clf = _build_classifier(self.algorithm, self.params)
        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", clf),
        ])

        t0 = time.perf_counter()
        self._pipeline.fit(X, y)
        duration_ms = (time.perf_counter() - t0) * 1000
        self._feature_cols = feature_cols

        cv_scores: dict[str, list[float]] = {}
        if cross_validate_model and len(np.unique(y)) >= 2:
            cv_scores = self._cross_validate(X, y, n_cv_folds)

        self._training_result = TrainingResult(
            algorithm=self.algorithm,
            feature_cols=feature_cols,
            classes=self.classes_,
            n_samples=len(X),
            duration_ms=duration_ms,
            cv_scores=cv_scores,
        )
        logger.info(
            "ClassificationService trained: algo=%s, n=%d, features=%d, "
            "classes=%d, duration=%.0fms%s",
            self.algorithm, len(X), len(feature_cols), len(self.classes_), duration_ms,
            f", cv_acc={self._training_result.cv_accuracy_mean:.4f}"
            if self._training_result.cv_accuracy_mean is not None else "",
        )
        return self._training_result

    def _cross_validate(
        self, X: np.ndarray, y: np.ndarray, n_folds: int
    ) -> dict[str, list[float]]:
        cv = StratifiedKFold(
            n_splits=n_folds, shuffle=True, random_state=DEFAULT_RANDOM_STATE
        )
        scoring = ["accuracy", "precision_weighted", "recall_weighted", "f1_weighted"]
        try:
            results = cross_validate(
                self._pipeline, X, y, cv=cv, scoring=scoring, n_jobs=-1
            )
            return {k: v.tolist() for k, v in results.items()}
        except Exception as exc:
            logger.warning("Validation croisée impossible : %s", exc)
            return {}

    # ── Prédiction ───────────────────────────────────────────────────────────

    def predict(self, data: list[dict]) -> PredictionResult:
        """
        Prédit les classes pour les données fournies.

        Returns:
            PredictionResult avec classes, probabilités et scores de confiance.
        """
        self._assert_trained()
        X = self._prepare(data)
        y_enc = self._pipeline.predict(X)
        classes = self._label_encoder.inverse_transform(y_enc).tolist()

        probas: Optional[list[list[float]]] = None
        confidence = [1.0] * len(classes)

        if hasattr(self._pipeline.named_steps["classifier"], "predict_proba"):
            raw = self._pipeline.predict_proba(X)
            probas = raw.tolist()
            confidence = raw.max(axis=1).tolist()

        return PredictionResult(classes=classes, probabilities=probas, confidence=confidence)

    def predict_proba(self, data: list[dict]) -> list[list[float]]:
        """Retourne les probabilités de classe. Lève ClassificationError si non disponible."""
        self._assert_trained()
        clf = self._pipeline.named_steps["classifier"]
        if not hasattr(clf, "predict_proba"):
            raise ClassificationError(
                f"L'algorithme '{self.algorithm}' ne supporte pas predict_proba."
            )
        return self._pipeline.predict_proba(self._prepare(data)).tolist()

    # ── Évaluation ───────────────────────────────────────────────────────────

    def evaluate(
        self,
        test_data: list[dict],
        target_col: str = "target",
    ) -> dict:
        """
        Évalue les performances sur un jeu de test.
        Retourne un dict compatible avec MLService._update_model_after_training().
        """
        self._assert_trained()
        df = self._to_df(test_data)
        self._check_target(df, target_col)

        y_raw = df[target_col].values
        known = set(self._label_encoder.classes_)
        mask = np.array([v in known for v in y_raw])
        if not mask.all():
            logger.warning(
                "%d observation(s) avec labels inconnus exclues.", (~mask).sum()
            )
            df = df[mask]
            y_raw = y_raw[mask]

        if len(y_raw) == 0:
            raise ValueError("Aucune observation valide après filtrage des labels inconnus.")

        X = self._prepare(test_data if mask.all() else df.to_dict("records"))
        y_enc = self._label_encoder.transform(y_raw)
        y_pred_enc = self._pipeline.predict(X)
        y_pred = self._label_encoder.inverse_transform(y_pred_enc)

        is_binary = len(self.classes_) == 2
        avg = "binary" if is_binary else "weighted"

        accuracy  = float(accuracy_score(y_raw, y_pred))
        precision = float(precision_score(y_raw, y_pred, average=avg, zero_division=0))
        recall    = float(recall_score(y_raw, y_pred, average=avg, zero_division=0))
        f1        = float(f1_score(y_raw, y_pred, average=avg, zero_division=0))
        cm        = confusion_matrix(y_raw, y_pred).tolist()
        report    = classification_report(y_raw, y_pred, zero_division=0)

        roc_auc: Optional[float] = None
        try:
            clf = self._pipeline.named_steps["classifier"]
            if hasattr(clf, "predict_proba"):
                probas = self._pipeline.predict_proba(X)
                if is_binary:
                    roc_auc = float(roc_auc_score(y_enc, probas[:, 1]))
                else:
                    roc_auc = float(
                        roc_auc_score(y_enc, probas, multi_class="ovr", average="weighted")
                    )
        except Exception as exc:
            logger.warning("ROC-AUC non calculable : %s", exc)

        result = EvaluationResult(
            accuracy=accuracy, precision=precision, recall=recall,
            f1_score=f1, roc_auc=roc_auc,
            confusion_matrix=cm, classification_report=report,
            n_samples=len(y_raw),
        )
        logger.info(
            "ClassificationService eval: acc=%.4f, f1=%.4f, roc_auc=%s, n=%d",
            accuracy, f1,
            f"{roc_auc:.4f}" if roc_auc is not None else "N/A",
            len(y_raw),
        )
        return result.to_dict()

    # ── Importances des features ──────────────────────────────────────────────

    def get_feature_importances(self) -> list[dict[str, Any]]:
        """
        Retourne les importances des features triées par rang décroissant.
        Disponible pour Random Forest, XGBoost, GradientBoosting,
        Logistic Regression.
        """
        self._assert_trained()
        clf = self._pipeline.named_steps["classifier"]
        importances: Optional[np.ndarray] = None

        if hasattr(clf, "feature_importances_"):
            importances = clf.feature_importances_
        elif hasattr(clf, "coef_"):
            coef = clf.coef_
            importances = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef[0])

        if importances is None:
            logger.info(
                "Importances non disponibles pour '%s'.", self.algorithm
            )
            return []

        idx = np.argsort(importances)[::-1]
        return [
            {
                "rank": rank + 1,
                "feature": self._feature_cols[i],
                "importance": round(float(importances[i]), 6),
            }
            for rank, i in enumerate(idx)
        ]

    # ── Persistance ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        self._assert_trained()
        joblib.dump({
            "pipeline": self._pipeline,
            "label_encoder": self._label_encoder,
            "feature_cols": self._feature_cols,
            "algorithm": self.algorithm,
            "config": self.config,
            "params": self.params,
        }, path, compress=3)
        logger.info("ClassificationService saved: path=%s, algo=%s", path, self.algorithm)

    def load(self, path: str) -> None:
        payload = joblib.load(path)
        self._pipeline = payload["pipeline"]
        self._label_encoder = payload["label_encoder"]
        self._feature_cols = payload["feature_cols"]
        logger.info(
            "ClassificationService loaded: path=%s, algo=%s",
            path, payload.get("algorithm", "unknown"),
        )

    # ── Méthodes privées ──────────────────────────────────────────────────────

    def _assert_trained(self) -> None:
        if not self.is_trained:
            raise ModelNotTrainedError(
                "Le modèle n'a pas encore été entraîné. Appelez train() d'abord."
            )

    @staticmethod
    def _to_df(data: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="ignore")
            except Exception:
                pass
        return df

    @staticmethod
    def _check_target(df: pd.DataFrame, target_col: str) -> None:
        if target_col not in df.columns:
            raise ValueError(
                f"Colonne target '{target_col}' absente. "
                f"Colonnes disponibles : {list(df.columns)}"
            )

    def _prepare(self, data: list[dict]) -> np.ndarray:
        """
        Prépare la matrice X à partir des données brutes.
        - Features manquantes → remplies avec FILL_MISSING_DEFAULT + warning
        - Features supplémentaires → ignorées
        """
        df = self._to_df(data)
        missing = set(self._feature_cols) - set(df.columns)
        extra = set(df.columns) - set(self._feature_cols)

        if missing:
            if len(missing) == len(self._feature_cols):
                raise FeatureMismatchError(
                    f"Aucune feature d'entraînement trouvée. Attendues : {self._feature_cols}"
                )
            logger.warning(
                "%d feature(s) manquante(s) remplacées par %.1f : %s",
                len(missing), FILL_MISSING_DEFAULT, sorted(missing),
            )
            for col in missing:
                df[col] = FILL_MISSING_DEFAULT

        if extra:
            logger.debug("%d colonne(s) supplémentaire(s) ignorées : %s", len(extra), sorted(extra))

        return df[self._feature_cols].values.astype(float)