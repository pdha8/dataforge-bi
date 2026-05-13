# apps/data_warehouse/routers.py
"""
Routeur de base de données pour Data Warehouse
"""
from django.conf import settings


class DataWarehouseRouter:
    """
    Routeur pour diriger les requêtes du Data Warehouse vers la base dédiée
    
    - Tous les modèles de l'app 'data_warehouse' vont dans 'data_warehouse_db'
    - Tous les autres modèles restent dans 'default'
    """
    
    def db_for_read(self, model, **hints):
        """
        Dirige les lectures vers la base appropriée
        """
        if model._meta.app_label == 'data_warehouse':
            return 'data_warehouse'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Dirige les écritures vers la base appropriée
        """
        if model._meta.app_label == 'data_warehouse':
            return 'data_warehouse'
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Autorise les relations entre objets de la même base
        """
        if obj1._state.db == obj2._state.db:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Contrôle où les migrations sont appliquées
        """
        if app_label == 'data_warehouse':
            return db == 'data_warehouse'
        elif db == 'data_warehouse':
            return False
        return db == 'default'