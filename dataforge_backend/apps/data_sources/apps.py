# apps/data_sources/apps.py
"""
Configuration de l'application data_sources pour Sotifibre
"""
from django.apps import AppConfig


class DataSourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.data_sources'
    label = 'data_sources'
    verbose_name = '🗄️ Data Sources - Gestion des sources de données BI'

    def ready(self):
        try:
            import apps.data_sources.signals
        except ImportError:
            pass
