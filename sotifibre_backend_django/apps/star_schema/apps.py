# apps/star_schema/apps.py
"""
Configuration de l'application star_schema pour Sotifibre
"""
from django.apps import AppConfig


class StarSchemaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.star_schema'
    label = 'star_schema'
    verbose_name = '⭐ Star Schema - Modélisation dimensionnelle avancée'

    def ready(self):
        try:
            import apps.star_schema.signals
        except ImportError:
            pass
