# apps/data_sources/signals.py
"""
Signaux pour l'application data_sources - Version optimisée
"""
import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import DataSource, DataSourceLog, DataSourceHistory
from apps.users.models import UserActivity

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=DataSource)
def data_source_pre_save(sender, instance, **kwargs):
    """Capture les changements avant sauvegarde"""
    if instance.pk:
        try:
            old_instance = DataSource.objects.get(pk=instance.pk)
            
            # Vérifier les changements importants
            if old_instance.status != instance.status:
                logger.info(f"📊 Statut changé: {old_instance.status} -> {instance.status}")
                
                DataSourceLog.objects.create(
                    data_source=instance,
                    level='info',
                    message=f"Statut changé de {old_instance.status} à {instance.status}"
                )
            
            # Enregistrer l'historique
            important_fields = [
                'name', 'description', 'source_type', 'status',
                'connection_string', 'host', 'port', 'database_name',
                'sync_frequency', 'auto_refresh_enabled'
            ]
            
            for field in important_fields:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    DataSourceHistory.objects.create(
                        data_source=instance,
                        field=field,
                        old_value=str(old_value) if old_value else '',
                        new_value=str(new_value) if new_value else '',
                    )
                    
        except DataSource.DoesNotExist:
            pass


@receiver(post_save, sender=DataSource)
def data_source_post_save(sender, instance, created, **kwargs):
    """Actions après sauvegarde"""
    if created:
        logger.info(f"✅ Nouvelle source de données créée: {instance.name}")
        
        DataSourceLog.objects.create(
            data_source=instance,
            level='info',
            message="Source de données créée"
        )
        
        # Journalisation pour les utilisateurs
        try:
            if hasattr(instance, '_request') and instance._request:
                UserActivity.objects.create(
                    user=instance._request.user,
                    action='create',
                    description=f"Source de données '{instance.name}' créée",
                    resource_type='data_source',
                    resource_id=str(instance.id),
                    resource_name=instance.name,
                    success=True
                )
        except:
            pass


@receiver(post_delete, sender=DataSource)
def data_source_post_delete(sender, instance, **kwargs):
    """Actions après suppression"""
    logger.info(f"🗑️ Source de données supprimée: {instance.name}")
    
    DataSourceLog.objects.create(
        data_source=instance,
        level='info',
        message="Source de données supprimée"
    )


@receiver(post_save, sender=DataSourceLog)
def data_source_log_post_save(sender, instance, created, **kwargs):
    """Actions après création d'un log"""
    if created and instance.level == 'error':
        logger.warning(f"⚠️ Erreur sur {instance.data_source.name}: {instance.message}")
        
        # Mettre à jour les erreurs de la source
        source = instance.data_source
        source.error_count += 1
        source.last_error = instance.message
        source.last_error_date = instance.created_at
        source.save(update_fields=['error_count', 'last_error', 'last_error_date'])


@receiver(post_save, sender=DataSourceHistory)
def data_source_history_post_save(sender, instance, created, **kwargs):
    """Actions après création d'un historique"""
    if created:
        logger.debug(f"📝 Historique: {instance.data_source.name} - {instance.field} modifié")