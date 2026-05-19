# apps/visualizations/signals.py
"""
Signaux pour l'application visualizations
"""
import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Dashboard, Widget, KPI, Report, VisualizationActivity

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dashboard)
def dashboard_pre_save(sender, instance, **kwargs):
    """Avant sauvegarde d'un tableau de bord"""
    if instance.pk:
        try:
            old_instance = Dashboard.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                logger.info(f"📊 Statut du dashboard changé: {old_instance.status} -> {instance.status}")
        except Dashboard.DoesNotExist:
            pass


@receiver(post_save, sender=Dashboard)
def dashboard_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'un tableau de bord"""
    action = "créé" if created else "modifié"
    logger.info(f"📊 Dashboard '{instance.name}' {action}")
    try:
        cache.delete_pattern(f"dashboard_{instance.id}_*")
    except AttributeError:
        cache.clear()


@receiver(post_delete, sender=Dashboard)
def dashboard_post_delete(sender, instance, **kwargs):
    """Après suppression d'un tableau de bord"""
    logger.info(f"🗑️ Dashboard '{instance.name}' supprimé")
    try:
        cache.delete_pattern(f"dashboard_{instance.id}_*")
    except AttributeError:
        pass


@receiver(post_save, sender=Widget)
def widget_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'un widget"""
    action = "créé" if created else "modifié"
    logger.info(f"📊 Widget '{instance.name}' {action}")
    try:
        cache.delete_pattern(f"widget_data_{instance.id}_*")
    except AttributeError:
        pass


@receiver(post_save, sender=KPI)
def kpi_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'un KPI"""
    action = "créé" if created else "modifié"
    logger.info(f"🎯 KPI '{instance.name}' {action}")


@receiver(post_save, sender=Report)
def report_post_save(sender, instance, created, **kwargs):
    """Après sauvegarde d'un rapport"""
    action = "créé" if created else "modifié"
    logger.info(f"📄 Rapport '{instance.name}' {action}")


@receiver(post_save, sender=VisualizationActivity)
def activity_post_save(sender, instance, created, **kwargs):
    """Après création d'une activité"""
    if created:
        logger.debug(f"📝 Activité: {instance.user} - {instance.activity_type} - {instance.description}")