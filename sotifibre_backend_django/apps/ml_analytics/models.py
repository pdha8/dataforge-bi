"""
apps/ml_analytics/models.py

Modèles Django pour l'application ML Analytics.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.users.models import User
from apps.star_schema.models import DimensionalSchema
from apps.data_warehouse.models import Measure

from .constants import (
    ANOMALY_SEVERITY,
    CONFIDENCE_LEVELS,
    FORECAST_PERIODS,
    MODEL_STATUS,
    MODEL_TYPES,
    ALGORITHMS,
    PRIORITY_LEVELS,
    QUALITY_THRESHOLDS,
    RECOMMENDATION_TYPES,
    TRAINING_FREQUENCIES,
    TRAINING_LOG_STATUS,
)
from .validators import validate_model_config, validate_forecast_params, validate_tags
from .managers import (
    AnomalyManager,
    ForecastManager,
    MLModelManager,
    ModelTrainingLogManager,
    RecommendationManager,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MLModel
# ─────────────────────────────────────────────────────────────────────────────

class MLModel(BaseModel):
    """
    Modèle de machine learning pour l'analytique prédictive.
    Supporte tous les types de modèles : prévision, anomalie,
    segmentation, recommandation, classification et Grok AI.
    """

    # Identification
    name = models.CharField("Nom", max_length=200, db_index=True)
    description = models.TextField("Description", blank=True)
    model_type = models.CharField(
        "Type de modèle", max_length=20, choices=MODEL_TYPES, db_index=True
    )
    algorithm = models.CharField(
        "Algorithme", max_length=30, choices=ALGORITHMS, db_index=True
    )
    status = models.CharField(
        "Statut", max_length=20, choices=MODEL_STATUS, default="pending", db_index=True
    )
    version = models.PositiveIntegerField("Version", default=1)

    # Source de données
    dimensional_schema = models.ForeignKey(
        DimensionalSchema,
        on_delete=models.CASCADE,
        related_name="ml_models",
        verbose_name="Schéma dimensionnel",
    )
    measure = models.ForeignKey(
        Measure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ml_models",
        verbose_name="Mesure cible",
    )

    # Configuration
    config = models.JSONField(
        "Configuration", default=dict, blank=True,
        validators=[validate_model_config],
    )
    parameters = models.JSONField("Paramètres", default=dict, blank=True)
    features = models.JSONField("Features", default=list, blank=True)

    # Métriques de performance
    accuracy = models.FloatField("Précision (%)", null=True, blank=True)
    precision = models.FloatField("Precision", null=True, blank=True)
    recall = models.FloatField("Recall", null=True, blank=True)
    f1_score = models.FloatField("F1 Score", null=True, blank=True)
    rmse = models.FloatField("RMSE", null=True, blank=True)
    mae = models.FloatField("MAE", null=True, blank=True)
    mape = models.FloatField("MAPE (%)", null=True, blank=True)
    roc_auc = models.FloatField("ROC-AUC", null=True, blank=True)

    # Entraînement
    last_trained = models.DateTimeField("Dernier entraînement", null=True, blank=True)
    training_frequency = models.CharField(
        "Fréquence d'entraînement", max_length=20,
        choices=TRAINING_FREQUENCIES, default="manual",
    )
    training_duration_ms = models.FloatField("Durée d'entraînement (ms)", null=True, blank=True)
    training_data_size = models.PositiveIntegerField(
        "Taille des données d'entraînement", null=True, blank=True
    )

    # Ownership
    is_active = models.BooleanField("Actif", default=True, db_index=True)
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="ml_models", verbose_name="Propriétaire",
    )
    team = models.ForeignKey(
        "users.Team", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ml_models", verbose_name="Équipe",
    )
    tags = models.JSONField(
        "Tags", default=list, blank=True, validators=[validate_tags]
    )

    # Fichiers sérialisés
    model_file = models.FileField(
        "Fichier modèle", upload_to="ml_models/%Y/%m/", blank=True
    )
    scaler_file = models.FileField(
        "Fichier scaler", upload_to="ml_models/%Y/%m/", blank=True
    )

    objects = MLModelManager()

    class Meta:
        db_table = "ml_models"
        ordering = ["-created_at"]
        verbose_name = "Modèle ML"
        verbose_name_plural = "Modèles ML"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["model_type", "status"]),
            models.Index(fields=["dimensional_schema"]),
            models.Index(fields=["owner", "team"]),
            models.Index(fields=["-last_trained"]),
            models.Index(fields=["is_active", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_model_type_display()}) v{self.version}"

    # ── Méthodes métier ──────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        """Vrai si le modèle peut effectuer des prédictions."""
        return self.status in ("trained", "deployed") and self.is_active

    def is_grok_model(self) -> bool:
        """Vrai si le modèle utilise le moteur Grok AI."""
        return self.algorithm == "grok" or self.model_type == "grok_insight"

    def get_performance_summary(self) -> dict[str, Any]:
        """
        Résumé structuré des métriques de performance.
        Utilisé par MLModelDetailSerializer.
        """
        quality = self._quality_label

        if self.model_type == "forecast":
            return {
                "type": "regression",
                "rmse": self._round(self.rmse, 4),
                "mae": self._round(self.mae, 4),
                "mape": self._round(self.mape, 2),
                "accuracy": self._round(self.accuracy, 2),
                "quality": quality,
            }
        if self.model_type in ("anomaly", "classification"):
            return {
                "type": "classification",
                "precision": self._round(self.precision, 4),
                "recall": self._round(self.recall, 4),
                "f1_score": self._round(self.f1_score, 4),
                "roc_auc": self._round(self.roc_auc, 4),
                "quality": quality,
            }
        if self.model_type == "grok_insight":
            return {"type": "llm", "engine": "Grok AI (xAI)", "quality": "N/A"}

        return {
            "type": "other",
            "accuracy": self._round(self.accuracy, 2),
            "quality": quality,
        }

    @property
    def _quality_label(self) -> str:
        if self.accuracy is None:
            return "non évalué"
        if self.accuracy >= QUALITY_THRESHOLDS["excellent"]:
            return "excellent"
        if self.accuracy >= QUALITY_THRESHOLDS["good"]:
            return "bon"
        if self.accuracy >= QUALITY_THRESHOLDS["acceptable"]:
            return "acceptable"
        return "à améliorer"

    @staticmethod
    def _round(value: Optional[float], ndigits: int) -> Optional[float]:
        return round(value, ndigits) if value is not None else None

    def train(self, data: Optional[list] = None) -> dict:
        from .services import MLService
        return MLService(self).train(data)

    def predict(self, data: dict) -> dict:
        from .services import MLService
        return MLService(self).predict(data)


# ─────────────────────────────────────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────────────────────────────────────

class Forecast(BaseModel):
    """Résultat de prévision généré par un modèle ML."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="forecasts"
    )
    name = models.CharField("Nom", max_length=200)
    description = models.TextField("Description", blank=True)

    forecast_period = models.CharField(
        "Période", max_length=20, choices=FORECAST_PERIODS, default="month"
    )
    horizon = models.PositiveIntegerField(
        "Horizon (nb de périodes)", default=12,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
    )
    confidence_level = models.PositiveIntegerField(
        "Niveau de confiance (%)", default=95, choices=CONFIDENCE_LEVELS
    )

    data = models.JSONField("Données prévues", default=list, blank=True)
    lower_bounds = models.JSONField("Bornes inférieures", default=list, blank=True)
    upper_bounds = models.JSONField("Bornes supérieures", default=list, blank=True)

    accuracy = models.FloatField("Précision", null=True, blank=True)
    mape = models.FloatField("MAPE (%)", null=True, blank=True)

    forecast_date = models.DateTimeField("Date de prévision")
    generated_at = models.DateTimeField("Généré le", auto_now_add=True)

    is_used = models.BooleanField("Utilisée", default=False, db_index=True)
    used_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="used_forecasts",
    )

    objects = ForecastManager()

    class Meta:
        db_table = "forecasts"
        ordering = ["-forecast_date"]
        verbose_name = "Prévision"
        verbose_name_plural = "Prévisions"
        indexes = [
            models.Index(fields=["model", "-forecast_date"]),
            models.Index(fields=["forecast_period"]),
            models.Index(fields=["is_used"]),
        ]

    def __str__(self) -> str:
        return f"{self.model.name} — {self.forecast_date.strftime('%Y-%m-%d')}"

    def get_chart_data(self) -> dict:
        return {
            "dates": [item["date"] for item in self.data],
            "values": [item["value"] for item in self.data],
            "lower_bounds": self.lower_bounds,
            "upper_bounds": self.upper_bounds,
            "confidence_level": self.confidence_level,
        }

    def get_summary(self) -> dict:
        if not self.data:
            return {"error": "Aucune donnée disponible."}
        values = [item["value"] for item in self.data]
        first, last = values[0], values[-1]
        trend_pct = ((last - first) / first * 100) if first != 0 else 0.0
        return {
            "min": min(values),
            "max": max(values),
            "avg": round(sum(values) / len(values), 4),
            "total": round(sum(values), 4),
            "first": first,
            "last": last,
            "trend": "up" if last > first else "down" if last < first else "stable",
            "trend_pct": round(trend_pct, 2),
            "n_points": len(values),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly
# ─────────────────────────────────────────────────────────────────────────────

class Anomaly(BaseModel):
    """Anomalie détectée par un modèle ML."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="anomalies"
    )
    dimensional_schema = models.ForeignKey(
        DimensionalSchema, on_delete=models.CASCADE, related_name="anomalies"
    )
    measure = models.ForeignKey(
        Measure, on_delete=models.SET_NULL, null=True, related_name="anomalies"
    )

    detected_at = models.DateTimeField("Détecté le", auto_now_add=True, db_index=True)
    date = models.DateField("Date de l'anomalie", db_index=True)
    value = models.FloatField("Valeur réelle")
    expected_value = models.FloatField("Valeur attendue")
    deviation = models.FloatField("Écart absolu")
    deviation_percentage = models.FloatField("Écart (%)")
    severity = models.CharField(
        "Sévérité", max_length=20, choices=ANOMALY_SEVERITY,
        default="medium", db_index=True,
    )

    is_confirmed = models.BooleanField("Confirmée", default=False)
    is_resolved = models.BooleanField("Résolue", default=False, db_index=True)
    resolved_at = models.DateTimeField("Résolue le", null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resolved_anomalies",
    )
    notes = models.TextField("Notes de résolution", blank=True)

    objects = AnomalyManager()

    class Meta:
        db_table = "anomalies"
        ordering = ["-detected_at"]
        verbose_name = "Anomalie"
        verbose_name_plural = "Anomalies"
        indexes = [
            models.Index(fields=["model", "-detected_at"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["date"]),
            models.Index(fields=["is_confirmed", "is_resolved"]),
        ]

    def __str__(self) -> str:
        return f"Anomalie {self.date} — Écart {self.deviation_percentage:.1f}%"

    def resolve(self, user: User, notes: str = "") -> None:
        """Marque l'anomalie comme résolue. Idempotente."""
        if self.is_resolved:
            return
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        if notes:
            self.notes = notes
        self.save(update_fields=["is_resolved", "resolved_at", "resolved_by", "notes"])

    def confirm(self) -> None:
        """Confirme l'anomalie. Idempotente."""
        if self.is_confirmed:
            return
        self.is_confirmed = True
        self.save(update_fields=["is_confirmed"])


# ─────────────────────────────────────────────────────────────────────────────
# SegmentationResult
# ─────────────────────────────────────────────────────────────────────────────

class SegmentationResult(BaseModel):
    """Résultat de segmentation (clustering) généré par un modèle ML."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="segmentations"
    )
    segment_name = models.CharField("Nom du segment", max_length=200)
    segment_description = models.TextField("Description", blank=True)
    segment_id = models.PositiveIntegerField("ID du segment")

    size = models.PositiveIntegerField("Nombre d'éléments", default=0)
    percentage = models.FloatField(
        "Pourcentage (%)", default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    characteristics = models.JSONField("Caractéristiques", default=dict)

    avg_value = models.FloatField("Valeur moyenne", null=True, blank=True)
    min_value = models.FloatField("Valeur min", null=True, blank=True)
    max_value = models.FloatField("Valeur max", null=True, blank=True)
    sum_value = models.FloatField("Somme", null=True, blank=True)

    class Meta:
        db_table = "segmentation_results"
        ordering = ["-percentage"]
        unique_together = [("model", "segment_id")]
        verbose_name = "Résultat de segmentation"
        verbose_name_plural = "Résultats de segmentation"
        indexes = [
            models.Index(fields=["model", "segment_id"]),
            models.Index(fields=["-percentage"]),
        ]

    def __str__(self) -> str:
        return f"{self.segment_name} ({self.percentage:.1f}%)"


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    """Recommandation générée par un modèle ML ou Grok."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="recommendations"
    )
    recommendation_type = models.CharField(
        "Type", max_length=20, choices=RECOMMENDATION_TYPES, db_index=True
    )
    target_id = models.UUIDField("ID de la cible")

    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description")
    confidence = models.FloatField(
        "Confiance (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    priority = models.CharField(
        "Priorité", max_length=20, choices=PRIORITY_LEVELS, default="medium"
    )

    score = models.FloatField("Score brut", null=True, blank=True)
    reason = models.TextField("Raison", blank=True)
    metadata = models.JSONField("Métadonnées", default=dict, blank=True)

    is_applied = models.BooleanField("Appliquée", default=False, db_index=True)
    applied_at = models.DateTimeField("Appliquée le", null=True, blank=True)
    applied_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="applied_recommendations",
    )
    is_dismissed = models.BooleanField("Ignorée", default=False, db_index=True)
    dismissed_at = models.DateTimeField("Ignorée le", null=True, blank=True)

    objects = RecommendationManager()

    class Meta:
        db_table = "recommendations"
        ordering = ["-confidence"]
        verbose_name = "Recommandation"
        verbose_name_plural = "Recommandations"
        indexes = [
            models.Index(fields=["model", "recommendation_type"]),
            models.Index(fields=["-confidence"]),
            models.Index(fields=["is_applied", "is_dismissed"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} (Confiance : {self.confidence:.0f}%)"

    def apply(self, user: User) -> None:
        """Marque la recommandation comme appliquée. Idempotente."""
        if self.is_applied:
            return
        self.is_applied = True
        self.applied_at = timezone.now()
        self.applied_by = user
        self.save(update_fields=["is_applied", "applied_at", "applied_by"])

    def dismiss(self) -> None:
        """Ignore la recommandation. Idempotente."""
        if self.is_dismissed:
            return
        self.is_dismissed = True
        self.dismissed_at = timezone.now()
        self.save(update_fields=["is_dismissed", "dismissed_at"])


# ─────────────────────────────────────────────────────────────────────────────
# ModelTrainingLog
# ─────────────────────────────────────────────────────────────────────────────

class ModelTrainingLog(BaseModel):
    """Journal d'entraînement d'un modèle ML."""

    model = models.ForeignKey(
        MLModel, on_delete=models.CASCADE, related_name="training_logs"
    )
    status = models.CharField(
        "Statut", max_length=20, choices=TRAINING_LOG_STATUS, db_index=True
    )
    error_message = models.TextField("Message d'erreur", blank=True)

    accuracy = models.FloatField("Précision", null=True, blank=True)
    loss = models.FloatField("Perte", null=True, blank=True)
    duration_ms = models.FloatField("Durée (ms)", null=True, blank=True)

    data_size = models.PositiveIntegerField("Taille des données", null=True, blank=True)
    batch_size = models.PositiveIntegerField("Taille de lot", null=True, blank=True)
    epochs = models.PositiveIntegerField("Époques", null=True, blank=True)

    started_at = models.DateTimeField("Démarré le")
    completed_at = models.DateTimeField("Terminé le", null=True, blank=True)

    objects = ModelTrainingLogManager()

    class Meta:
        db_table = "model_training_logs"
        ordering = ["-started_at"]
        verbose_name = "Journal d'entraînement"
        verbose_name_plural = "Journaux d'entraînement"
        indexes = [
            models.Index(fields=["model", "-started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Log {self.model.name} — {self.status} ({self.started_at.date()})"
