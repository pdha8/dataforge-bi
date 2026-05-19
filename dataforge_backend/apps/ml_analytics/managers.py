"""
apps/ml_analytics/managers.py

Managers Django pour tous les modèles ML Analytics.
Encapsule la logique de requêtes complexes hors des vues et services.
"""
from __future__ import annotations

from datetime import timedelta

from django.db import models
from django.db.models import Avg, Count, Q
from django.utils import timezone


class MLModelManager(models.Manager):

    def active(self) -> models.QuerySet:
        return self.filter(is_active=True)

    def by_type(self, model_type: str) -> models.QuerySet:
        return self.filter(model_type=model_type)

    def by_owner(self, user) -> models.QuerySet:
        return self.filter(owner=user)

    def trained(self) -> models.QuerySet:
        return self.filter(status="trained")

    def deployed(self) -> models.QuerySet:
        return self.filter(status="deployed")

    def ready(self) -> models.QuerySet:
        """Modèles prêts à effectuer des prédictions (trained ou deployed)."""
        return self.filter(status__in=("trained", "deployed"), is_active=True)

    def needs_training(self) -> models.QuerySet:
        """
        Retourne les modèles actifs qui ont besoin d'être (ré)entraînés,
        en fonction de leur fréquence d'entraînement configurée.

        Utilise des filtres DB purs (Q objects) — aucune boucle Python,
        donc une seule requête SQL quelle que soit la taille de la table.
        """
        now = timezone.now()

        pending_or_failed = Q(is_active=True, status__in=("pending", "failed"))

        hourly_overdue = Q(
            is_active=True, status="trained",
            training_frequency="hourly",
            last_trained__lt=now - timedelta(hours=1),
        )
        daily_overdue = Q(
            is_active=True, status="trained",
            training_frequency="daily",
            last_trained__lt=now - timedelta(days=1),
        )
        weekly_overdue = Q(
            is_active=True, status="trained",
            training_frequency="weekly",
            last_trained__lt=now - timedelta(weeks=1),
        )
        monthly_overdue = Q(
            is_active=True, status="trained",
            training_frequency="monthly",
            last_trained__lt=now - timedelta(days=30),
        )

        return self.filter(
            pending_or_failed
            | hourly_overdue
            | daily_overdue
            | weekly_overdue
            | monthly_overdue
        )

    def performance_stats(self) -> dict:
        """Statistiques agrégées de performance sur tous les modèles."""
        return self.aggregate(
            avg_accuracy=Avg("accuracy"),
            avg_f1=Avg("f1_score"),
            avg_rmse=Avg("rmse"),
            total=Count("id"),
        )


class ForecastManager(models.Manager):

    def for_model(self, model) -> models.QuerySet:
        return self.filter(model=model)

    def recent(self, days: int = 30) -> models.QuerySet:
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(forecast_date__gte=cutoff)

    def unused(self) -> models.QuerySet:
        return self.filter(is_used=False)

    def latest_for_model(self, model) -> models.QuerySet:
        return self.filter(model=model).order_by("-forecast_date").first()


class AnomalyManager(models.Manager):

    def unresolved(self) -> models.QuerySet:
        return self.filter(is_resolved=False)

    def by_severity(self, severity: str) -> models.QuerySet:
        return self.filter(severity=severity)

    def critical_unresolved(self) -> models.QuerySet:
        return self.filter(severity="critical", is_resolved=False)

    def recent(self, days: int = 7) -> models.QuerySet:
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(detected_at__gte=cutoff)

    def severity_counts(self) -> dict:
        return dict(
            self.values_list("severity").annotate(count=Count("id"))
        )


class RecommendationManager(models.Manager):

    def active(self) -> models.QuerySet:
        return self.filter(is_applied=False, is_dismissed=False)

    def by_confidence(self, min_confidence: float = 0.0) -> models.QuerySet:
        return self.filter(confidence__gte=min_confidence)

    def high_priority(self) -> models.QuerySet:
        return self.active().filter(priority="high").order_by("-confidence")


class ModelTrainingLogManager(models.Manager):

    def for_model(self, model) -> models.QuerySet:
        return self.filter(model=model)

    def successful(self) -> models.QuerySet:
        return self.filter(status="completed")

    def failed(self) -> models.QuerySet:
        return self.filter(status="failed")

    def recent(self, days: int = 7) -> models.QuerySet:
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(started_at__gte=cutoff)
