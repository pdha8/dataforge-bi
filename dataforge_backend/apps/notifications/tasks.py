# apps/notifications/tasks.py
"""
Tâches Celery pour l'application notifications
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .services import NotificationService, AlertRuleService
from .models import Notification

logger = logging.getLogger(__name__)


@shared_task
def check_alert_rules():
    """Vérifie toutes les règles d'alerte"""
    logger.info("Démarrage de la vérification des règles d'alerte")
    try:
        service = AlertRuleService()
        service.check_all_rules()
        logger.info("Vérification des règles d'alerte terminée")
        return {'status': 'success', 'checked': True}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des règles: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def send_pending_notifications():
    """Envoie les notifications en attente"""
    logger.info("Démarrage de l'envoi des notifications en attente")
    notifications = Notification.objects.filter(status='pending')
    service = NotificationService()
    
    sent_count = 0
    failed_count = 0
    
    for notification in notifications:
        for channel in notification.channels:
            result = service.send(notification, channel)
            if result['success']:
                sent_count += 1
            else:
                failed_count += 1
    
    logger.info(f"Notifications envoyées: {sent_count}, échouées: {failed_count}")
    return {'sent': sent_count, 'failed': failed_count}


@shared_task
def clean_old_notifications(days=30):
    """Nettoie les anciennes notifications"""
    cutoff = timezone.now() - timedelta(days=days)
    deleted_count = Notification.objects.filter(
        created_at__lt=cutoff,
        status__in=['read', 'archived']
    ).delete()[0]
    
    logger.info(f"{deleted_count} anciennes notifications supprimées")
    return {'deleted': deleted_count}


@shared_task
def send_weekly_digest(user_id):
    """Envoie un digest hebdomadaire des notifications"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        cutoff = timezone.now() - timedelta(days=7)
        
        notifications = Notification.objects.filter(
            recipient=user,
            created_at__gte=cutoff
        )
        
        if notifications.exists():
            service = NotificationService()
            service.create_notification(
                recipient=user,
                notification_type='weekly_digest',
                title="Votre digest hebdomadaire",
                message=f"Vous avez reçu {notifications.count()} notifications cette semaine",
                priority='low'
            )
            logger.info(f"Digest hebdomadaire envoyé à {user.email}")
            return {'sent': True, 'user': user.email, 'count': notifications.count()}
        else:
            logger.info(f"Aucune notification pour {user.email} cette semaine")
            return {'sent': False, 'user': user.email, 'count': 0}
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du digest: {e}")
        return {'status': 'error', 'error': str(e)}