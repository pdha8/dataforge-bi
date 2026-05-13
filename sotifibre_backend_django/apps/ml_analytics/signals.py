"""
apps/ml_analytics/signals.py

Signaux Django pour l'application ML Analytics.
Découple la logique de logging et de side-effects des modèles.
"""
from __future__ import annotations

import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Anomaly, MLModel, ModelTrainingLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MLModel)
def ml_model_post_save(sender, instance: MLModel, created: bool, **kwargs) -> None:
    action = "créé" if created else "mis à jour"
    logger.info(
        "🤖 MLModel '%s' (id=%s, type=%s, algo=%s) %s.",
        instance.name, instance.pk, instance.model_type, instance.algorithm, action,
    )


@receiver(post_delete, sender=MLModel)
def ml_model_post_delete(sender, instance: MLModel, **kwargs) -> None:
    logger.info("🗑️ MLModel '%s' (id=%s) supprimé.", instance.name, instance.pk)


@receiver(pre_save, sender=MLModel)
def ml_model_pre_save(sender, instance: MLModel, **kwargs) -> None:
    """Incrémente la version à chaque passage en statut 'trained'."""
    if instance.pk:
        try:
            previous = MLModel.objects.only("status").get(pk=instance.pk)
            if previous.status != "trained" and instance.status == "trained":
                # La version est déjà incrémentée par MLService.
                # Ce signal sert uniquement à logger le changement de statut.
                logger.info(
                    "🏋️ MLModel '%s' vient d'être entraîné (v%s).",
                    instance.name, instance.version,
                )
        except MLModel.DoesNotExist:
            pass


@receiver(post_save, sender=Anomaly)
def anomaly_post_save(sender, instance: Anomaly, created: bool, **kwargs) -> None:
    if created:
        logger.info(
            "🔍 Anomalie détectée : modèle='%s', date=%s, sévérité=%s, écart=%.1f%%.",
            instance.model.name, instance.date,
            instance.severity, instance.deviation_percentage,
        )


@receiver(post_save, sender=ModelTrainingLog)
def training_log_post_save(
    sender, instance: ModelTrainingLog, created: bool, **kwargs
) -> None:
    if not created and instance.status == "failed":
        logger.error(
            "❌ Entraînement échoué : modèle='%s', erreur=%s",
            instance.model.name, instance.error_message[:200],
        )
    elif not created and instance.status == "completed":
        logger.info(
            "✅ Entraînement terminé : modèle='%s', durée=%.0fms.",
            instance.model.name, instance.duration_ms or 0,
        )
