"""
apps/ml_analytics/filters.py

Filtres django-filter pour tous les modèles ML Analytics.
"""
from django_filters import rest_framework as filters
from django.db.models import Q

from .models import Anomaly, Forecast, MLModel, ModelTrainingLog, Recommendation
from .constants import (
    ALGORITHMS,
    ANOMALY_SEVERITY,
    FORECAST_PERIODS,
    MODEL_STATUS,
    MODEL_TYPES,
    PRIORITY_LEVELS,
    RECOMMENDATION_TYPES,
    TRAINING_FREQUENCIES,
    TRAINING_LOG_STATUS,
)


class MLModelFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    description = filters.CharFilter(lookup_expr="icontains")
    model_type = filters.ChoiceFilter(choices=MODEL_TYPES)
    algorithm = filters.ChoiceFilter(choices=ALGORITHMS)
    status = filters.ChoiceFilter(choices=MODEL_STATUS)
    training_frequency = filters.ChoiceFilter(choices=TRAINING_FREQUENCIES)
    is_active = filters.BooleanFilter()

    owner = filters.UUIDFilter(field_name="owner__id")
    team = filters.UUIDFilter(field_name="team__id")
    dimensional_schema = filters.UUIDFilter(field_name="dimensional_schema__id")
    measure = filters.UUIDFilter(field_name="measure__id")

    min_accuracy = filters.NumberFilter(field_name="accuracy", lookup_expr="gte")
    max_accuracy = filters.NumberFilter(field_name="accuracy", lookup_expr="lte")
    min_f1 = filters.NumberFilter(field_name="f1_score", lookup_expr="gte")

    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    last_trained_after = filters.DateTimeFilter(field_name="last_trained", lookup_expr="gte")
    last_trained_before = filters.DateTimeFilter(field_name="last_trained", lookup_expr="lte")

    search = filters.CharFilter(method="filter_search", label="Recherche globale")

    class Meta:
        model = MLModel
        fields = ["model_type", "algorithm", "status", "is_active", "owner", "team"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class ForecastFilter(filters.FilterSet):
    model = filters.UUIDFilter(field_name="model__id")
    forecast_period = filters.ChoiceFilter(choices=FORECAST_PERIODS)
    is_used = filters.BooleanFilter()
    forecast_date_after = filters.DateTimeFilter(field_name="forecast_date", lookup_expr="gte")
    forecast_date_before = filters.DateTimeFilter(field_name="forecast_date", lookup_expr="lte")
    generated_after = filters.DateTimeFilter(field_name="generated_at", lookup_expr="gte")
    min_accuracy = filters.NumberFilter(field_name="accuracy", lookup_expr="gte")

    class Meta:
        model = Forecast
        fields = ["model", "forecast_period", "is_used"]


class AnomalyFilter(filters.FilterSet):
    model = filters.UUIDFilter(field_name="model__id")
    dimensional_schema = filters.UUIDFilter(field_name="dimensional_schema__id")
    measure = filters.UUIDFilter(field_name="measure__id")
    severity = filters.ChoiceFilter(choices=ANOMALY_SEVERITY)
    is_confirmed = filters.BooleanFilter()
    is_resolved = filters.BooleanFilter()

    date_after = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = filters.DateFilter(field_name="date", lookup_expr="lte")
    detected_after = filters.DateTimeFilter(field_name="detected_at", lookup_expr="gte")
    detected_before = filters.DateTimeFilter(field_name="detected_at", lookup_expr="lte")

    min_deviation = filters.NumberFilter(field_name="deviation_percentage", lookup_expr="gte")

    class Meta:
        model = Anomaly
        fields = ["model", "dimensional_schema", "severity", "is_confirmed", "is_resolved"]


class RecommendationFilter(filters.FilterSet):
    model = filters.UUIDFilter(field_name="model__id")
    recommendation_type = filters.ChoiceFilter(choices=RECOMMENDATION_TYPES)
    priority = filters.ChoiceFilter(choices=PRIORITY_LEVELS)
    is_applied = filters.BooleanFilter()
    is_dismissed = filters.BooleanFilter()
    min_confidence = filters.NumberFilter(field_name="confidence", lookup_expr="gte")
    max_confidence = filters.NumberFilter(field_name="confidence", lookup_expr="lte")

    class Meta:
        model = Recommendation
        fields = ["model", "recommendation_type", "priority", "is_applied", "is_dismissed"]


class ModelTrainingLogFilter(filters.FilterSet):
    model = filters.UUIDFilter(field_name="model__id")
    status = filters.ChoiceFilter(choices=TRAINING_LOG_STATUS)
    started_after = filters.DateTimeFilter(field_name="started_at", lookup_expr="gte")
    started_before = filters.DateTimeFilter(field_name="started_at", lookup_expr="lte")
    completed_after = filters.DateTimeFilter(field_name="completed_at", lookup_expr="gte")
    completed_before = filters.DateTimeFilter(field_name="completed_at", lookup_expr="lte")
    min_duration_ms = filters.NumberFilter(field_name="duration_ms", lookup_expr="gte")

    class Meta:
        model = ModelTrainingLog
        fields = ["model", "status"]
