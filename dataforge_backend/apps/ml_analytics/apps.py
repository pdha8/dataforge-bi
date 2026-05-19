"""
apps/ml_analytics/apps.py
"""
from django.apps import AppConfig


class MLAnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ml_analytics"
    label = "ml_analytics"
    verbose_name = "🤖 ML Analytics — Intelligence Artificielle & Prédictions"

    def ready(self) -> None:
        try:
            import apps.ml_analytics.signals  # noqa: F401
        except ImportError:
            pass
