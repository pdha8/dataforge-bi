"""
apps/ml_analytics/tasks.py

Tâches Celery pour l'application ML Analytics.
Toutes les tâches sont thin wrappers autour des services métier.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from .models import MLModel
from .services import MLService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def train_scheduled_models(self) -> dict:
    """
    Entraîne tous les modèles actifs dont la fréquence d'entraînement
    est dépassée. Appelée par Celery Beat.
    """
    models = MLModel.objects.needs_training().select_related(
        "dimensional_schema", "measure", "owner"
    )
    total = models.count()
    succeeded, failed = 0, 0

    for model in models:
        try:
            logger.info("⏳ Démarrage de l'entraînement : '%s' (id=%s)", model.name, model.pk)
            result = MLService(model).train()
            if result["success"]:
                succeeded += 1
                logger.info("✅ Entraînement réussi : '%s'", model.name)
            else:
                failed += 1
                logger.warning("⚠️ Entraînement échoué : '%s' — %s", model.name, result.get("error"))
        except Exception as exc:
            failed += 1
            logger.exception("❌ Erreur inattendue pour '%s' : %s", model.name, exc)
            # Retry automatique Celery si erreur réseau ou transitoire
            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error("⛔ Nombre maximum de tentatives atteint pour '%s'.", model.name)

    logger.info(
        "🔁 train_scheduled_models terminé : total=%d, succès=%d, échec=%d",
        total, succeeded, failed,
    )
    return {"total": total, "succeeded": succeeded, "failed": failed}


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def run_anomaly_detection(self) -> dict:
    """
    Lance la détection d'anomalies sur tous les modèles actifs de type 'anomaly'.
    Appelée périodiquement par Celery Beat.
    """
    models = MLModel.objects.filter(
        model_type="anomaly", is_active=True, status__in=("trained", "deployed")
    ).select_related("dimensional_schema", "measure", "owner")

    total_anomalies = 0
    processed = 0

    for model in models:
        try:
            service = MLService(model)
            data = service._get_training_data()
            if not data:
                logger.warning(
                    "Pas de données disponibles pour la détection — modèle '%s'.", model.name
                )
                continue
            result = service.predict({"data": data})
            if result["success"]:
                n = result.get("count", 0)
                total_anomalies += n
                processed += 1
                logger.info("🔍 '%s' : %d anomalie(s) détectée(s).", model.name, n)
        except Exception as exc:
            logger.exception("Erreur de détection pour '%s' : %s", model.name, exc)
            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                pass

    logger.info(
        "🔁 run_anomaly_detection terminé : modèles traités=%d, anomalies=%d",
        processed, total_anomalies,
    )
    return {"processed": processed, "total_anomalies": total_anomalies}


@shared_task
def cleanup_old_training_logs(days: int = 90) -> dict:
    """
    Supprime les logs d'entraînement plus anciens que `days` jours.
    Appelée hebdomadairement par Celery Beat.
    """
    from .models import ModelTrainingLog

    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted, _ = ModelTrainingLog.objects.filter(started_at__lt=cutoff).delete()
    logger.info("🧹 %d log(s) d'entraînement supprimé(s) (antérieurs à %s).", deleted, cutoff.date())
    return {"deleted": deleted}


@shared_task
def generate_model_stats() -> dict:
    """
    Calcule et retourne les statistiques globales des modèles ML.
    Peut être utilisée pour alimenter un dashboard de monitoring.
    """
    stats = MLModel.objects.performance_stats()
    by_type = dict(
        MLModel.objects.values_list("model_type").annotate(
            count=__import__("django.db.models", fromlist=["Count"]).Count("id")
        )
    )
    by_status = dict(
        MLModel.objects.values_list("status").annotate(
            count=__import__("django.db.models", fromlist=["Count"]).Count("id")
        )
    )
    result = {
        **stats,
        "by_type": by_type,
        "by_status": by_status,
        "generated_at": timezone.now().isoformat(),
    }
    logger.info("📊 Statistiques ML générées : %s", result)
    return result