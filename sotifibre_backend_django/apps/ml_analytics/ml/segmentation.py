"""
apps/ml_analytics/ml/segmentation.py

Service de segmentation (clustering) pour ML Analytics.
Supporte : K-Means, DBSCAN, Hierarchical (Agglomerative).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Segment:
    segment_id: int
    size: int
    percentage: float
    characteristics: dict[str, float]
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sum_value: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "segment_name": f"Segment {self.segment_id}",
            "size": self.size,
            "percentage": round(self.percentage, 2),
            "characteristics": {k: round(v, 4) for k, v in self.characteristics.items()},
            "avg_value": round(self.avg_value, 4) if self.avg_value is not None else None,
            "min_value": round(self.min_value, 4) if self.min_value is not None else None,
            "max_value": round(self.max_value, 4) if self.max_value is not None else None,
            "sum_value": round(self.sum_value, 4) if self.sum_value is not None else None,
        }


@dataclass
class SegmentationResult:
    algorithm: str
    n_segments: int
    n_samples: int
    segments: list[Segment]
    silhouette: Optional[float] = None
    davies_bouldin: Optional[float] = None
    calinski_harabasz: Optional[float] = None
    labels: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "n_segments": self.n_segments,
            "n_samples": self.n_samples,
            "segments": [s.to_dict() for s in self.segments],
            "metrics": {
                "silhouette": round(self.silhouette, 4) if self.silhouette is not None else None,
                "davies_bouldin": round(self.davies_bouldin, 4) if self.davies_bouldin is not None else None,
                "calinski_harabasz": round(self.calinski_harabasz, 2) if self.calinski_harabasz is not None else None,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class SegmentationError(Exception):
    """Erreur de base pour le service de segmentation."""


class SegmentorNotFittedError(SegmentationError):
    """Le modèle n'a pas encore été entraîné."""


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class SegmentationService:
    """
    Service de segmentation (clustering) non supervisé.

    data attendu : [{"feature1": val, "feature2": val, ...}, ...]
    """

    def __init__(self, model_instance):
        self.model = model_instance
        self.config: dict = model_instance.config
        self.params: dict = model_instance.parameters
        self._clusterer: Optional[Any] = None
        self._scaler: Optional[StandardScaler] = None
        self._feature_cols: list[str] = []
        self._result: Optional[SegmentationResult] = None

    @property
    def is_fitted(self) -> bool:
        return self._clusterer is not None and self._scaler is not None

    # ── Entraînement ─────────────────────────────────────────────────────────

    def train(self, data: list[dict]) -> SegmentationResult:
        if not data:
            raise SegmentationError("Le dataset d'entraînement est vide.")

        df = pd.DataFrame(data).select_dtypes(include=[np.number])
        if df.empty:
            raise SegmentationError("Aucune colonne numérique trouvée dans les données.")

        self._feature_cols = df.columns.tolist()
        self._scaler = StandardScaler()
        X = self._scaler.fit_transform(df.values)

        algo = self.model.algorithm
        dispatch = {
            "kmeans":       self._fit_kmeans,
            "dbscan":       self._fit_dbscan,
            "hierarchical": self._fit_hierarchical,
        }
        fitter = dispatch.get(algo)
        if fitter is None:
            raise SegmentationError(f"Algorithme de segmentation non supporté : '{algo}'.")

        labels = fitter(X)
        self._result = self._build_result(df, X, labels)
        logger.info(
            "SegmentationService trained: algo=%s, n=%d, segments=%d",
            algo, len(data), self._result.n_segments,
        )
        return self._result

    def _fit_kmeans(self, X: np.ndarray) -> np.ndarray:
        k = self.params.get("n_clusters", 4)
        self._clusterer = KMeans(
            n_clusters=k,
            init=self.params.get("init", "k-means++"),
            n_init=self.params.get("n_init", 10),
            max_iter=self.params.get("max_iter", 300),
            random_state=42,
        )
        return self._clusterer.fit_predict(X)

    def _fit_dbscan(self, X: np.ndarray) -> np.ndarray:
        self._clusterer = DBSCAN(
            eps=self.params.get("eps", 0.5),
            min_samples=self.params.get("min_samples", 5),
            metric=self.params.get("metric", "euclidean"),
            n_jobs=-1,
        )
        return self._clusterer.fit_predict(X)

    def _fit_hierarchical(self, X: np.ndarray) -> np.ndarray:
        self._clusterer = AgglomerativeClustering(
            n_clusters=self.params.get("n_clusters", 4),
            linkage=self.params.get("linkage", "ward"),
        )
        return self._clusterer.fit_predict(X)

    def _build_result(
        self, df: pd.DataFrame, X: np.ndarray, labels: np.ndarray
    ) -> SegmentationResult:
        unique_labels = [l for l in np.unique(labels) if l != -1]  # -1 = bruit DBSCAN
        n_samples = len(labels)
        segments = []

        for seg_id in unique_labels:
            mask = labels == seg_id
            subset = df[mask]
            characteristics = {col: float(subset[col].mean()) for col in self._feature_cols}
            value_col = self.config.get("value_column")
            if value_col and value_col in subset.columns:
                vals = subset[value_col]
                avg_v, min_v, max_v, sum_v = float(vals.mean()), float(vals.min()), float(vals.max()), float(vals.sum())
            else:
                avg_v = min_v = max_v = sum_v = None

            segments.append(Segment(
                segment_id=int(seg_id),
                size=int(mask.sum()),
                percentage=round(mask.sum() / n_samples * 100, 2),
                characteristics=characteristics,
                avg_value=avg_v,
                min_value=min_v,
                max_value=max_v,
                sum_value=sum_v,
            ))

        # Métriques de clustering (uniquement si >= 2 segments)
        silhouette = davies_bouldin = calinski_harabasz = None
        valid_mask = labels != -1
        if len(unique_labels) >= 2 and valid_mask.sum() > len(unique_labels):
            try:
                silhouette = float(silhouette_score(X[valid_mask], labels[valid_mask]))
                davies_bouldin = float(davies_bouldin_score(X[valid_mask], labels[valid_mask]))
                calinski_harabasz = float(calinski_harabasz_score(X[valid_mask], labels[valid_mask]))
            except Exception as e:
                logger.warning("Métriques de clustering non calculables : %s", e)

        return SegmentationResult(
            algorithm=self.model.algorithm,
            n_segments=len(unique_labels),
            n_samples=n_samples,
            segments=sorted(segments, key=lambda s: s.percentage, reverse=True),
            silhouette=silhouette,
            davies_bouldin=davies_bouldin,
            calinski_harabasz=calinski_harabasz,
            labels=labels.tolist(),
        )

    # ── Prédiction ────────────────────────────────────────────────────────────

    def predict(self, data: list[dict]) -> list[int]:
        """Assigne les nouvelles observations aux segments existants."""
        self._assert_fitted()
        df = pd.DataFrame(data)
        for col in self._feature_cols:
            if col not in df.columns:
                df[col] = 0.0
        X = self._scaler.transform(df[self._feature_cols].values)
        if hasattr(self._clusterer, "predict"):
            return self._clusterer.predict(X).tolist()
        # DBSCAN / AgglomerativeClustering n'ont pas de predict — on utilise le centroïde le plus proche
        if hasattr(self._clusterer, "cluster_centers_"):
            centers = self._clusterer.cluster_centers_
            dists = np.linalg.norm(X[:, None] - centers[None, :], axis=2)
            return dists.argmin(axis=1).tolist()
        raise SegmentationError(
            f"L'algorithme '{self.model.algorithm}' ne supporte pas la prédiction sur nouvelles données."
        )

    # ── Évaluation ────────────────────────────────────────────────────────────

    def evaluate(self, test_data: list[dict]) -> dict:
        if self._result is None:
            return {"error": "Modèle non entraîné."}
        return self._result.to_dict()

    # ── Persistance ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        self._assert_fitted()
        joblib.dump({
            "clusterer": self._clusterer,
            "scaler": self._scaler,
            "feature_cols": self._feature_cols,
            "result": self._result,
        }, path, compress=3)
        logger.info("SegmentationService saved: path=%s", path)

    def load(self, path: str) -> None:
        payload = joblib.load(path)
        self._clusterer = payload["clusterer"]
        self._scaler = payload["scaler"]
        self._feature_cols = payload["feature_cols"]
        self._result = payload.get("result")

    def _assert_fitted(self) -> None:
        if not self.is_fitted:
            raise SegmentorNotFittedError("Le modèle n'a pas encore été entraîné.")
