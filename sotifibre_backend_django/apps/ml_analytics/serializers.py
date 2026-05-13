"""
apps/ml_analytics/serializers.py

Serializers DRF pour tous les modèles ML Analytics.
"""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    Anomaly,
    Forecast,
    MLModel,
    ModelTrainingLog,
    Recommendation,
    SegmentationResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# MLModel
# ─────────────────────────────────────────────────────────────────────────────

class MLModelSerializer(serializers.ModelSerializer):
    model_type_display = serializers.CharField(
        source="get_model_type_display", read_only=True
    )
    algorithm_display = serializers.CharField(
        source="get_algorithm_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    training_frequency_display = serializers.CharField(
        source="get_training_frequency_display", read_only=True
    )
    owner_name = serializers.CharField(
        source="owner.get_full_name", read_only=True, default=None
    )
    team_name = serializers.CharField(
        source="team.name", read_only=True, default=None
    )
    dimensional_schema_name = serializers.CharField(
        source="dimensional_schema.name", read_only=True
    )
    measure_name = serializers.CharField(
        source="measure.name", read_only=True, default=None
    )
    is_ready = serializers.SerializerMethodField()

    class Meta:
        model = MLModel
        fields = [
            "id", "name", "description",
            "model_type", "model_type_display",
            "algorithm", "algorithm_display",
            "status", "status_display",
            "version",
            "dimensional_schema", "dimensional_schema_name",
            "measure", "measure_name",
            "config", "parameters", "features",
            "accuracy", "precision", "recall", "f1_score",
            "rmse", "mae", "mape", "roc_auc",
            "last_trained", "training_frequency", "training_frequency_display",
            "training_duration_ms", "training_data_size",
            "is_active", "is_ready",
            "owner", "owner_name",
            "team", "team_name",
            "tags",
            "model_file", "scaler_file",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "version",
            "accuracy", "precision", "recall", "f1_score",
            "rmse", "mae", "mape", "roc_auc",
            "last_trained", "training_duration_ms", "training_data_size",
            "created_at", "updated_at",
        ]

    def get_is_ready(self, obj: MLModel) -> bool:
        return obj.is_ready()


class MLModelDetailSerializer(MLModelSerializer):
    """Serializer détaillé incluant le résumé de performance."""
    performance_summary = serializers.SerializerMethodField()
    forecasts_count = serializers.SerializerMethodField()
    anomalies_count = serializers.SerializerMethodField()
    recommendations_count = serializers.SerializerMethodField()

    class Meta(MLModelSerializer.Meta):
        fields = MLModelSerializer.Meta.fields + [
            "performance_summary",
            "forecasts_count",
            "anomalies_count",
            "recommendations_count",
        ]

    def get_performance_summary(self, obj: MLModel) -> dict:
        return obj.get_performance_summary()

    def get_forecasts_count(self, obj: MLModel) -> int:
        return obj.forecasts.count()

    def get_anomalies_count(self, obj: MLModel) -> int:
        return obj.anomalies.count()

    def get_recommendations_count(self, obj: MLModel) -> int:
        return obj.recommendations.count()


class MLModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = [
            "name", "description",
            "model_type", "algorithm",
            "dimensional_schema", "measure",
            "config", "parameters", "features",
            "training_frequency",
            "is_active", "owner", "team", "tags",
        ]

    def validate(self, attrs: dict) -> dict:
        model_type = attrs.get("model_type")
        algorithm = attrs.get("algorithm")
        # Grok insight doit utiliser l'algorithme grok
        if model_type == "grok_insight" and algorithm != "grok":
            raise serializers.ValidationError(
                {"algorithm": "Le type 'grok_insight' requiert l'algorithme 'grok'."}
            )
        return attrs


class MLModelPredictSerializer(serializers.Serializer):
    data = serializers.JSONField(
        required=False, default=list,
        help_text="Données d'entrée pour la prédiction.",
    )
    horizon = serializers.IntegerField(
        required=False, min_value=1, max_value=365,
        help_text="Horizon de prévision en nombre de périodes.",
    )
    user_id = serializers.CharField(
        required=False, allow_blank=True,
        help_text="Identifiant utilisateur pour les recommandations.",
    )
    items = serializers.ListField(
        child=serializers.CharField(), required=False, default=list,
        help_text="Liste d'items pour le filtrage collaboratif.",
    )
    n = serializers.IntegerField(
        required=False, default=5, min_value=1, max_value=100,
        help_text="Nombre de recommandations à retourner.",
    )
    context = serializers.JSONField(
        required=False, default=dict,
        help_text="Contexte métier pour les insights Grok.",
    )
    target_col = serializers.CharField(
        required=False, default="target",
        help_text="Nom de la colonne cible (classification).",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────────────────────────────────────

class ForecastSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source="model.name", read_only=True)
    forecast_period_display = serializers.CharField(
        source="get_forecast_period_display", read_only=True
    )
    used_by_name = serializers.CharField(
        source="used_by.get_full_name", read_only=True, default=None
    )
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Forecast
        fields = "__all__"
        read_only_fields = ["id", "generated_at", "created_at", "updated_at"]

    def get_summary(self, obj: Forecast) -> dict:
        return obj.get_summary()


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly
# ─────────────────────────────────────────────────────────────────────────────

class AnomalySerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )
    model_name = serializers.CharField(source="model.name", read_only=True)
    dimensional_schema_name = serializers.CharField(
        source="dimensional_schema.name", read_only=True
    )
    measure_name = serializers.CharField(
        source="measure.name", read_only=True, default=None
    )
    resolved_by_name = serializers.CharField(
        source="resolved_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Anomaly
        fields = "__all__"
        read_only_fields = ["id", "detected_at", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# SegmentationResult
# ─────────────────────────────────────────────────────────────────────────────

class SegmentationResultSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source="model.name", read_only=True)

    class Meta:
        model = SegmentationResult
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationSerializer(serializers.ModelSerializer):
    recommendation_type_display = serializers.CharField(
        source="get_recommendation_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    model_name = serializers.CharField(source="model.name", read_only=True)
    applied_by_name = serializers.CharField(
        source="applied_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = Recommendation
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# ModelTrainingLog
# ─────────────────────────────────────────────────────────────────────────────

class ModelTrainingLogSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    model_name = serializers.CharField(source="model.name", read_only=True)

    class Meta:
        model = ModelTrainingLog
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
