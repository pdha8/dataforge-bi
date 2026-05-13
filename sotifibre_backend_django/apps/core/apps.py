# apps/core/apps.py
"""
Configuration de l'application core pour Sotifibre
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'apps.core'
    verbose_name = "⚙️ Core - Utilitaires de base Sotifibre"

    def ready(self):
        # Importer les signaux
        try:
            import apps.core.signals
        except ImportError:
            pass
