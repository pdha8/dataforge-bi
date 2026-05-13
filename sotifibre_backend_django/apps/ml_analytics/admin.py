"""
apps/ml_analytics/admin.py

Administration Django pour l'application ML Analytics.
"""
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from .models import (
    Anomaly,
    Forecast,
    MLModel,
    ModelTrainingLog,
    Recommendation,
    SegmentationResult,
)

# ─── Couleurs par statut ─────────────────────────────────────────────────────

_STATUS_COLORS = {
    "pending":    "secondary",
    "training":   "warning",
    "trained":    "success",
    "failed":     "danger",
    "deployed":   "primary",
    "deprecated": "dark",
    "archived":   "secondary",
}

_SEVERITY_COLORS = {
    "low":      "success",
    "medium":   "warning",
    "high":     "orange",
    "critical": "danger",
}


def _badge(text: str, color: str) -> str:
    return format_html(
        '<span style="padding:2px 8px;border-radius:4px;font-size:12px;'
        'background:var(--{}-bg,#eee);color:var(--{}-fg,#333)">{}</span>',
        color, color, text,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MLModel
# ─────────────────────────────────────────────────────────────────────────────

class TrainingLogInline(admin.TabularInline):
    model = ModelTrainingLog
    extra = 0
    max_num = 10
    fields = ("status", "started_at", "completed_at", "duration_ms", "accuracy", "error_message")
    readonly_fields = fields
    ordering = ("-started_at",)
    can_delete = False


@admin.register(MLModel)
class MLModelAdmin(ImportExportModelAdmin):
    list_display = [
        "name", "model_type_badge", "algorithm_badge", "status_badge",
        "version", "accuracy_display", "last_trained", "is_active",
    ]
    list_filter = ["model_type", "algorithm", "status", "is_active", "training_frequency"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "version", "last_trained", "training_duration_ms", "training_data_size",
        "accuracy", "precision", "recall", "f1_score", "rmse", "mae", "mape", "roc_auc",
        "created_at", "updated_at",
    ]
    inlines = [TrainingLogInline]
    fieldsets = (
        ("Identification", {
            "fields": ("name", "description", "model_type", "algorithm", "status", "version", "is_active"),
        }),
        ("Source de données", {
            "fields": ("dimensional_schema", "measure"),
        }),
        ("Configuration", {
            "fields": ("config", "parameters", "features"),
            "classes": ("collapse",),
        }),
        ("Métriques de performance", {
            "fields": ("accuracy", "precision", "recall", "f1_score", "rmse", "mae", "mape", "roc_auc"),
            "classes": ("collapse",),
        }),
        ("Entraînement", {
            "fields": ("training_frequency", "last_trained", "training_duration_ms", "training_data_size"),
        }),
        ("Ownership", {
            "fields": ("owner", "team", "tags"),
        }),
        ("Fichiers sérialisés", {
            "fields": ("model_file", "scaler_file"),
            "classes": ("collapse",),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def model_type_badge(self, obj: MLModel):
        return format_html('<span class="badge bg-primary">{}</span>', obj.get_model_type_display())
    model_type_badge.short_description = "Type"

    def algorithm_badge(self, obj: MLModel):
        return format_html('<span class="badge bg-info">{}</span>', obj.get_algorithm_display())
    algorithm_badge.short_description = "Algorithme"

    def status_badge(self, obj: MLModel):
        color = _STATUS_COLORS.get(obj.status, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>', color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def accuracy_display(self, obj: MLModel):
        if obj.accuracy is None:
            return "—"
        color = "success" if obj.accuracy >= 85 else "warning" if obj.accuracy >= 70 else "danger"
        return format_html(
            '<span class="badge bg-{}">{:.1f}%</span>', color, obj.accuracy
        )
    accuracy_display.short_description = "Précision"


# ─────────────────────────────────────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Forecast)
class ForecastAdmin(ImportExportModelAdmin):
    list_display = ["name", "model", "forecast_period", "horizon", "forecast_date", "accuracy", "is_used"]
    list_filter = ["forecast_period", "is_used", "confidence_level"]
    search_fields = ["name", "model__name"]
    readonly_fields = ["generated_at", "created_at", "updated_at"]


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Anomaly)
class AnomalyAdmin(ImportExportModelAdmin):
    list_display = [
        "model", "date", "value", "expected_value",
        "severity_badge", "is_confirmed", "is_resolved", "detected_at",
    ]
    list_filter = ["severity", "is_confirmed", "is_resolved"]
    search_fields = ["model__name", "notes"]
    readonly_fields = ["detected_at", "created_at", "updated_at"]
    date_hierarchy = "date"

    def severity_badge(self, obj: Anomaly):
        color = _SEVERITY_COLORS.get(obj.severity, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>', color, obj.get_severity_display()
        )
    severity_badge.short_description = "Sévérité"


# ─────────────────────────────────────────────────────────────────────────────
# SegmentationResult
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(SegmentationResult)
class SegmentationResultAdmin(ImportExportModelAdmin):
    list_display = ["segment_name", "model", "segment_id", "size", "percentage", "avg_value"]
    list_filter = ["model"]
    search_fields = ["segment_name", "model__name"]


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Recommendation)
class RecommendationAdmin(ImportExportModelAdmin):
    list_display = [
        "title", "model", "recommendation_type",
        "confidence_display", "priority", "is_applied", "is_dismissed",
    ]
    list_filter = ["recommendation_type", "priority", "is_applied", "is_dismissed"]
    search_fields = ["title", "description", "model__name"]
    readonly_fields = ["applied_at", "dismissed_at", "created_at", "updated_at"]

    def confidence_display(self, obj: Recommendation):
        color = "success" if obj.confidence >= 80 else "warning" if obj.confidence >= 50 else "danger"
        return format_html(
            '<span class="badge bg-{}">{:.0f}%</span>', color, obj.confidence
        )
    confidence_display.short_description = "Confiance"


# ─────────────────────────────────────────────────────────────────────────────
# ModelTrainingLog
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(ModelTrainingLog)
class ModelTrainingLogAdmin(ImportExportModelAdmin):
    list_display = [
        "model", "status_badge", "data_size",
        "duration_display", "started_at", "completed_at",
    ]
    list_filter = ["status"]
    search_fields = ["model__name", "error_message"]
    readonly_fields = ["started_at", "completed_at", "created_at", "updated_at"]

    def status_badge(self, obj: ModelTrainingLog):
        colors = {
            "started": "primary", "in_progress": "warning",
            "completed": "success", "failed": "danger",
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, "secondary"),
            obj.get_status_display(),
        )
    status_badge.short_description = "Statut"

    def duration_display(self, obj: ModelTrainingLog):
        if obj.duration_ms is None:
            return "—"
        if obj.duration_ms < 1000:
            return format_html("<b>{:.0f}</b> ms", obj.duration_ms)
        return format_html("<b>{:.1f}</b> s", obj.duration_ms / 1000)
    duration_display.short_description = "Durée"