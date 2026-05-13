"""
apps/ml_analytics/ml/recommendation.py

Service de recommandation : filtrage collaboratif, content-based, hybride.
"""
from __future__ import annotations

import logging
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class RecommendationError(Exception):
    pass


class RecommendationService:
    """
    Service de recommandation (collaboratif, content-based, hybride).

    CORRECTION vs version initiale :
    - _item_index séparé de user_item_matrix.columns
      pour éviter KeyError en mode content-based pur.
    """

    def __init__(self, model_instance):
        self.model = model_instance
        self.config: dict = model_instance.config
        self.params: dict = model_instance.parameters
        self._user_item_matrix: Optional[pd.DataFrame] = None
        self._similarity_matrix: Optional[np.ndarray] = None
        self._item_index: list = []

    @property
    def is_fitted(self) -> bool:
        return self._similarity_matrix is not None

    # ── Entraînement ─────────────────────────────────────────────────────────

    def train(self, data: dict) -> None:
        algo = self.model.algorithm
        if algo == "collaborative_filtering":
            self.train_collaborative_filtering(data.get("interactions", []))
        elif algo == "content_based":
            self.train_content_based(data.get("items", []), data.get("features", []))
        else:
            self.train_collaborative_filtering(data.get("interactions", []))
            self.train_content_based(data.get("items", []), data.get("features", []))

    def train_collaborative_filtering(self, interactions: list[dict]) -> None:
        if not interactions:
            raise RecommendationError("Interactions vides pour le filtrage collaboratif.")
        df = pd.DataFrame(interactions)
        self._user_item_matrix = df.pivot_table(
            index="user_id", columns="item_id",
            values="interaction_score", fill_value=0,
        )
        self._item_index = list(self._user_item_matrix.columns)
        self._similarity_matrix = cosine_similarity(self._user_item_matrix.T)
        logger.info(
            "Collaborative filtering: %d users, %d items.",
            len(self._user_item_matrix), len(self._item_index),
        )

    def train_content_based(self, items: list, features: list[str]) -> None:
        if not items or not features:
            raise RecommendationError("Items ou features vides pour le mode content-based.")
        if len(items) != len(features):
            raise RecommendationError("items et features doivent avoir la même longueur.")
        self._item_index = list(items)
        vectorizer = TfidfVectorizer()
        vecs = vectorizer.fit_transform(features)
        self._similarity_matrix = cosine_similarity(vecs)
        logger.info("Content-based filtering: %d items.", len(items))

    # ── Recommandations ───────────────────────────────────────────────────────

    def get_recommendations(
        self, user_id: Optional[str], items: list, n: int = 5
    ) -> list:
        algo = self.model.algorithm
        if algo == "collaborative_filtering":
            return self._collaborative(user_id, n)
        if algo == "content_based":
            return self._content_based(items, n)
        return self._hybrid(user_id, items, n)

    def _collaborative(self, user_id: Optional[str], n: int) -> list:
        if self._user_item_matrix is None or user_id not in self._user_item_matrix.index:
            return []
        user_items = self._user_item_matrix.loc[user_id]
        liked = set(user_items[user_items > 0].index)
        scores: dict = {}
        for item in liked:
            if item not in self._item_index:
                continue
            idx = self._item_index.index(item)
            for i, s in enumerate(self._similarity_matrix[idx]):
                other = self._item_index[i]
                if other not in liked:
                    scores[other] = scores.get(other, 0.0) + float(s)
        return [k for k, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]]

    def _content_based(self, items: list, n: int) -> list:
        if self._similarity_matrix is None or not self._item_index:
            return []
        scores: dict = {}
        for item in items:
            if item not in self._item_index:
                continue
            idx = self._item_index.index(item)
            for i, s in enumerate(self._similarity_matrix[idx]):
                other = self._item_index[i]
                if other != item:
                    scores[other] = max(scores.get(other, 0.0), float(s))
        return [k for k, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]]

    def _hybrid(self, user_id: Optional[str], items: list, n: int) -> list:
        coll = self._collaborative(user_id, n)
        cont = self._content_based(items, n)
        all_scores: dict = {}
        for r in coll[:n]:
            all_scores[r] = all_scores.get(r, 0.0) + 0.6
        for r in cont[:n]:
            all_scores[r] = all_scores.get(r, 0.0) + 0.4
        return [k for k, _ in sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:n]]

    # ── Évaluation ────────────────────────────────────────────────────────────

    def evaluate(self, test_interactions: list[dict]) -> dict:
        precision_scores, recall_scores = [], []
        for interaction in test_interactions:
            actual = set(interaction.get("items", []))
            if not actual:
                continue
            recommended = set(self.get_recommendations(
                interaction.get("user_id"), list(actual), n=10
            ))
            hits = len(recommended & actual)
            precision_scores.append(hits / len(recommended) if recommended else 0.0)
            recall_scores.append(hits / len(actual))
        if not precision_scores:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        p, r = float(np.mean(precision_scores)), float(np.mean(recall_scores))
        f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}

    # ── Persistance ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        joblib.dump({
            "user_item_matrix": self._user_item_matrix,
            "similarity_matrix": self._similarity_matrix,
            "item_index": self._item_index,
        }, path, compress=3)

    def load(self, path: str) -> None:
        payload = joblib.load(path)
        self._user_item_matrix = payload["user_item_matrix"]
        self._similarity_matrix = payload["similarity_matrix"]
        self._item_index = payload["item_index"]
