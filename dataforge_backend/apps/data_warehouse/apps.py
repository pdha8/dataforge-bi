# apps/data_warehouse/apps.py
"""
Configuration de l'application data_warehouse pour Sotifibre
"""
from django.apps import AppConfig


class DataWarehouseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.data_warehouse'
    label = 'data_warehouse'
    verbose_name = '🏢 Data Warehouse - Entrepôt de données BI'

    def ready(self):
        try:
            import apps.data_warehouse.signals
        except ImportError:
            pass
