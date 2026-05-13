# apps/etl_engine/signals.py
"""
Signaux pour l'application etl_engine
"""
import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import ETLPipeline, ExecutionLog
from apps.users.models import UserActivity

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ETLPipeline)
def etl_pipeline_pre_save(sender, instance, **kwargs):
    """Capture les changements avant sauvegarde"""
    if instance.pk:
        try:
            old_instance = ETLPipeline.objects.get(pk=instance.pk)
            
            if old_instance.status != instance.status:
                logger.info(f"📊 Statut pipeline changé: {old_instance.status} -> {instance.status}")
            
            if old_instance.schedule_enabled != instance.schedule_enabled:
                if instance.schedule_enabled:
                    instance.calculate_next_execution()
                else:
                    instance.next_execution = None
                    
        except ETLPipeline.DoesNotExist:
            pass


@receiver(post_save, sender=ETLPipeline)
def etl_pipeline_post_save(sender, instance, created, **kwargs):
    """Actions après sauvegarde"""
    if created:
        logger.info(f"✅ Nouveau pipeline ETL créé: {instance.name}")
        
        try:
            if hasattr(instance, '_request') and instance._request:
                UserActivity.objects.create(
                    user=instance._request.user,
                    action='create',
                    description=f"Pipeline ETL '{instance.name}' créé",
                    resource_type='etl_pipeline',
                    resource_id=str(instance.id),
                    resource_name=instance.name,
                    success=True
                )
        except:
            pass


@receiver(post_save, sender=ExecutionLog)
def execution_log_post_save(sender, instance, created, **kwargs):
    """Actions après création d'un log d'exécution"""
    if created:
        logger.info(f"📝 Exécution pipeline: {instance.pipeline.name} - {instance.status}")
        
        if instance.status == 'failed':
            logger.error(f"❌ Échec pipeline {instance.pipeline.name}: {instance.error_message}")