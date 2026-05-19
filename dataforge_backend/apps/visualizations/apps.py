# apps/visualizations/apps.py
"""
Configuration de l'application visualizations pour Sotifibre
"""
from django.apps import AppConfig


class VisualizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.visualizations'
    label = 'visualizations'
    verbose_name = '📊 Visualizations - Tableaux de bord BI avancés'

    def ready(self):
        try:
            import apps.visualizations.signals
        except ImportError:
            pass
