# apps/star_schema/signals.py
"""
Signaux pour l'application star_schema
"""
import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import StarSchema, CustomCalculation

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=StarSchema)
def star_schema_pre_save(sender, instance, **kwargs):
    """Avant sauvegarde d'un schéma en étoile"""
    if instance.pk:
        try:
            old_instance = StarSchema.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                logger.info(f"⭐ Statut du schéma changé: {old_instance.status} -> {instance.status}")
        except StarSchema.DoesNotExist:
            pass


@receiver(post_save, sender=StarSchema)
def star_schema_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'un schéma en étoile"""
    action = "créé" if created else "modifié"
    logger.info(f"⭐ Schéma en étoile '{instance.name}' {action}")
    
    # Invalider le cache
    cache.delete_pattern(f"star_schema_{instance.id}_*")


@receiver(post_delete, sender=StarSchema)
def star_schema_post_delete(sender, instance, **kwargs):
    """Après suppression d'un schéma en étoile"""
    logger.info(f"🗑️ Schéma en étoile '{instance.name}' supprimé")
    cache.delete_pattern(f"star_schema_{instance.id}_*")


@receiver(post_save, sender=CustomCalculation)
def custom_calculation_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'un calcul personnalisé"""
    action = "créé" if created else "modifié"
    logger.info(f"📊 Calcul personnalisé '{instance.name}' {action}")
    
    # Invalider le cache du schéma associé
    cache.delete_pattern(f"star_schema_{instance.star_schema.id}_*")