# apps/etl_engine/apps.py
"""
Configuration de l'application etl_engine pour Sotifibre
"""
from django.apps import AppConfig


class ETLEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.etl_engine'
    label = 'etl_engine'
    verbose_name = '🔄 ETL Engine - Moteur d\'intégration de données'

    def ready(self):
        try:
            import apps.etl_engine.signals
        except ImportError:
            pass
