# apps/data_warehouse/signals.py
"""
Signaux pour l'application data_warehouse
"""
import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import DataWarehouseTable, DataWarehouseLog
from apps.users.models import UserActivity

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=DataWarehouseTable)
def data_warehouse_table_pre_save(sender, instance, **kwargs):
    """Capture les changements avant sauvegarde"""
    if instance.pk:
        try:
            old_instance = DataWarehouseTable.objects.get(pk=instance.pk)
            
            if old_instance.status != instance.status:
                logger.info(f"📊 Statut table changé: {old_instance.status} -> {instance.status}")
                
                DataWarehouseLog.objects.create(
                    table=instance,
                    operation='refresh',
                    level='info',
                    message=f"Statut changé de {old_instance.status} à {instance.status}"
                )
                
        except DataWarehouseTable.DoesNotExist:
            pass


@receiver(post_save, sender=DataWarehouseTable)
def data_warehouse_table_post_save(sender, instance, created, **kwargs):
    """Actions après sauvegarde"""
    if created:
        logger.info(f"✅ Nouvelle table Data Warehouse créée: {instance.full_name}")
        
        DataWarehouseLog.objects.create(
            table=instance,
            operation='refresh',
            level='info',
            message="Table créée"
        )
        
        # Mettre à jour le compteur du schéma
        instance.schema.table_count = instance.schema.tables.count()
        instance.schema.save(update_fields=['table_count'])
        
        try:
            if hasattr(instance, '_request') and instance._request:
                UserActivity.objects.create(
                    user=instance._request.user,
                    action='create',
                    description=f"Table Data Warehouse '{instance.full_name}' créée",
                    resource_type='dw_table',
                    resource_id=str(instance.id),
                    resource_name=instance.full_name,
                    success=True
                )
        except:
            pass


@receiver(post_delete, sender=DataWarehouseTable)
def data_warehouse_table_post_delete(sender, instance, **kwargs):
    """Actions après suppression"""
    logger.info(f"🗑️ Table Data Warehouse supprimée: {instance.full_name}")
    
    DataWarehouseLog.objects.create(
        table=instance,
        operation='refresh',
        level='info',
        message="Table supprimée"
    )
    
    # Mettre à jour le compteur du schéma
    if instance.schema:
        instance.schema.table_count = instance.schema.tables.count()
        instance.schema.save(update_fields=['table_count'])