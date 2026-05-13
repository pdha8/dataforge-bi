# apps/notifications/signals.py
"""
Signaux pour l'application notifications
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Notification, AlertRule
from .services import NotificationService, AlertRuleService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'une notification"""
    if created:
        logger.info(f"🔔 Notification créée: {instance.title} pour {instance.recipient.email}")
        
        # Envoyer la notification en temps réel via WebSocket
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer and async_to_sync:
                async_to_sync(channel_layer.group_send)(
                    f"user_{instance.recipient.id}",
                    {
                        'type': 'notification_message',
                        'notification': {
                            'id': str(instance.id),
                            'title': instance.title,
                            'message': instance.message,
                            'type': instance.notification_type,
                            'priority': instance.priority,
                            'icon': instance.get_icon(),
                            'color': instance.get_color(),
                            'created_at': instance.created_at.isoformat()
                        }
                    }
                )
        except ImportError:
            logger.debug("Channels non disponible, WebSocket désactivé")
        except Exception as e:
            logger.error(f"Erreur WebSocket: {e}")


@receiver(post_save, sender=AlertRule)
def alert_rule_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'une règle d'alerte"""
    action = "créée" if created else "modifiée"
    logger.info(f"⚡ Règle d'alerte '{instance.name}' {action}")


@receiver(post_delete, sender=AlertRule)
def alert_rule_post_delete(sender, instance, **kwargs):
    """Après suppression d'une règle d'alerte"""
    logger.info(f"🗑️ Règle d'alerte '{instance.name}' supprimée")