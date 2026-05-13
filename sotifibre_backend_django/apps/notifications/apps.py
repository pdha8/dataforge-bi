# apps/notifications/apps.py
"""
Configuration de l'application notifications pour Sotifibre
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    label = 'notifications'
    verbose_name = '🔔 Notifications - Alertes et communications BI'

    def ready(self):
        try:
            import apps.notifications.signals
        except ImportError:
            pass
