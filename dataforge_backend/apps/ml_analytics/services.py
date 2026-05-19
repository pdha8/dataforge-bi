"""
apps/ml_analytics/services.py

Orchestrateur ML — route les appels vers le bon service ML
selon le type et l'algorithme du modèle.

Corrections vs version initiale :
- Guard _save_model_if_supported() : évite AttributeError sur GrokService
- Dispatch predict() via table de handlers (lisible et extensible)
- model.save(update_fields=...) : évite d'écraser des champs non liés
- _update_model_after_training() : méthode isolée et claire
- _get_training_data() : gestion d'erreurs robuste
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from django.core.files.base import ContentFile
from django.utils import timezone

from apps.notifications.services import NotificationService
from apps.star_schema.services import DimensionalSchemaService

from .models import Anomaly, MLModel, ModelTrainingLog, Recommendation
from .ml.anomaly_detection import AnomalyDetectionService
from .ml.classification import ClassificationService
from .ml.forecasting import ForecastingService
from .ml.grok import GrokService
from .ml.recommendation import RecommendationService
from .ml.segmentation import SegmentationService

logger = logging.getLogger(__name__)


class MLService:
    """
    Orchestrateur pour les modèles ML Analytics.

    Route automatiquement vers le bon service sous-jacent
    (GrokService, ForecastingService, AnomalyDetectionService, etc.)
    selon model.model_type et model.algorithm.
    """

    def __init__(self, model: MLModel) -> None:
        self.model = model

    # ────────────────────────────────────────────────────────────────────────
    # Résolution du service
    # ────────────────────────────────────────────────────────────────────────

    def get_service(self):
        """Instancie et retourne le service ML approprié."""
        if self.model.is_grok_model():
            return GrokService(self.model)

        dispatch = {
            "forecast":       ForecastingService,
            "anomaly":        AnomalyDetectionService,
            "recommendation": RecommendationService,
            "classification": ClassificationService,
            "segmentation":   SegmentationService,
        }
        service_class = dispatch.get(self.model.model_type)
        if service_class is None:
            raise ValueError(
                f"Type de modèle non supporté : '{self.model.model_type}'. "
                f"Types disponibles : {list(dispatch.keys())}"
            )
        return service_class(self.model)

    # ────────────────────────────────────────────────────────────────────────
    # Entraînement
    # ────────────────────────────────────────────────────────────────────────

    def train(self, data: Optional[list] = None) -> dict:
        """
        Entraîne le modèle.
        Pour Grok, marque simplement le modèle comme entraîné (service cloud).
        """
        # ── Cas Grok : pas d'entraînement réel ──────────────────────────────
        if self.model.is_grok_model():
            self.model.status = "trained"
            self.model.last_trained = timezone.now()
            self.model.save(update_fields=["status", "last_trained", "updated_at"])
            logger.info("Grok model '%s' marqué comme entraîné.", self.model.name)
            return {"success": True, "message": "Grok model ready.", "model": self.model}

        # ── Données d'entraînement ───────────────────────────────────────────
        if not data:
            data = self._get_training_data()
        if not data:
            return {
                "success": False,
                "error": "Aucune donnée d'entraînement disponible.",
            }

        # ── Log + statut ─────────────────────────────────────────────────────
        log = ModelTrainingLog.objects.create(
            model=self.model,
            status="started",
            started_at=timezone.now(),
            data_size=len(data),
        )
        self.model.status = "training"
        self.model.save(update_fields=["status", "updated_at"])

        # ── Entraînement ─────────────────────────────────────────────────────
        try:
            service = self.get_service()
            t0 = time.perf_counter()
            service.train(data)
            duration_ms = (time.perf_counter() - t0) * 1000

            evaluation = self._safe_evaluate(service, data)
            self._update_model_after_training(duration_ms, len(data), evaluation)

            log.status = "completed"
            log.completed_at = timezone.now()
            log.duration_ms = duration_ms
            log.save(update_fields=["status", "completed_at", "duration_ms"])

            self._save_model_if_supported(service)
            self._notify("training_completed")

            logger.info(
                "Modèle '%s' entraîné avec succès en %.0fms.", self.model.name, duration_ms
            )
            return {
                "success": True,
                "model": self.model,
                "duration_ms": round(duration_ms, 2),
            }

        except Exception as exc:
            logger.exception(
                "Erreur d'entraînement pour '%s' : %s", self.model.name, exc
            )
            self.model.status = "failed"
            self.model.save(update_fields=["status", "updated_at"])
            log.status = "failed"
            log.error_message = str(exc)
            log.completed_at = timezone.now()
            log.save(update_fields=["status", "error_message", "completed_at"])
            self._notify("training_failed", str(exc))
            return {"success": False, "error": str(exc)}

    # ────────────────────────────────────────────────────────────────────────
    # Prédiction
    # ────────────────────────────────────────────────────────────────────────

    def predict(self, data: dict) -> dict:
        """
        Effectue une prédiction selon le type du modèle.
        Retourne toujours un dict avec 'success' (bool) et les résultats.
        """
        if not self.model.is_ready():
            return {
                "success": False,
                "error": f"Modèle non prêt (statut : {self.model.status}).",
            }

        service = self.get_service()
        handlers = {
            "grok_insight":   self._predict_grok,
            "forecast":       self._predict_forecast,
            "anomaly":        self._predict_anomaly,
            "recommendation": self._predict_recommendation,
            "classification": self._predict_classification,
            "segmentation":   self._predict_segmentation,
        }
        handler = handlers.get(self.model.model_type)
        if handler is None:
            return {
                "success": False,
                "error": f"Type non supporté : '{self.model.model_type}'.",
            }
        try:
            return handler(service, data)
        except Exception as exc:
            logger.exception(
                "Erreur de prédiction pour '%s' : %s", self.model.name, exc
            )
            return {"success": False, "error": str(exc)}

    # ── Handlers de prédiction ────────────────────────────────────────────────

    def _predict_grok(self, service: GrokService, data: dict) -> dict:
        insight = service.generate_insight(
            data.get("data", []),
            data.get("context"),
        )
        return {"success": True, "insight": insight, "type": "insight"}

    def _predict_forecast(self, service: ForecastingService, data: dict) -> dict:
        horizon = int(data.get("horizon") or self.model.config.get("default_horizon", 30))
        result = service.forecast(horizon)
        return {"success": True, "data": result, "type": "forecast", "horizon": horizon}

    def _predict_anomaly(self, service: AnomalyDetectionService, data: dict) -> dict:
        anomalies = service.detect(data.get("data", []))
        saved = self._save_anomalies(anomalies)
        return {
            "success": True,
            "anomalies": saved,
            "count": len(saved),
            "type": "anomaly",
        }

    def _predict_recommendation(self, service: RecommendationService, data: dict) -> dict:
        recs = service.get_recommendations(
            user_id=data.get("user_id"),
            items=data.get("items", []),
            n=int(data.get("n", 5)),
        )
        saved = self._save_recommendations(recs)
        return {"success": True, "recommendations": saved, "type": "recommendation"}

    def _predict_classification(self, service: ClassificationService, data: dict) -> dict:
        result = service.predict(data.get("data", []))
        return {"success": True, "result": result.to_dict(), "type": "classification"}

    def _predict_segmentation(self, service: SegmentationService, data: dict) -> dict:
        labels = service.predict(data.get("data", []))
        return {"success": True, "labels": labels, "type": "segmentation"}

    # ────────────────────────────────────────────────────────────────────────
    # Méthodes privées
    # ────────────────────────────────────────────────────────────────────────

    def _get_training_data(self) -> list:
        """Récupère les données d'entraînement depuis le schéma dimensionnel."""
        try:
            schema_svc = DimensionalSchemaService(self.model.dimensional_schema)
            result = schema_svc.execute(limit=10_000)
            if not result.get("success") or not result.get("data"):
                logger.warning(
                    "Aucune donnée retournée par le schéma '%s'.",
                    self.model.dimensional_schema.name,
                )
                return []
            column = self.model.measure.column if self.model.measure else "value"
            return [
                {"date": row["date"], "value": row.get(column, 0)}
                for row in result["data"]
                if "date" in row
            ]
        except Exception as exc:
            logger.error("Erreur lors de la récupération des données : %s", exc)
            return []

    def _safe_evaluate(self, service: Any, data: list) -> Optional[dict]:
        """Évalue le modèle sans propager les exceptions."""
        try:
            return service.evaluate(data)
        except Exception as exc:
            logger.warning("Évaluation impossible : %s", exc)
            return None

    def _update_model_after_training(
        self,
        duration_ms: float,
        data_size: int,
        evaluation: Optional[dict],
    ) -> None:
        """Met à jour les métriques et métadonnées du modèle après entraînement."""
        update_fields = [
            "status", "last_trained", "version",
            "training_duration_ms", "training_data_size", "updated_at",
        ]
        self.model.status = "trained"
        self.model.last_trained = timezone.now()
        self.model.version += 1
        self.model.training_duration_ms = duration_ms
        self.model.training_data_size = data_size

        if evaluation:
            if self.model.model_type == "forecast":
                self.model.rmse = evaluation.get("rmse")
                self.model.mae = evaluation.get("mae")
                self.model.mape = evaluation.get("mape")
                self.model.accuracy = evaluation.get("accuracy")
                update_fields += ["rmse", "mae", "mape", "accuracy"]
            elif self.model.model_type in ("anomaly", "classification"):
                self.model.precision = evaluation.get("precision")
                self.model.recall = evaluation.get("recall")
                self.model.f1_score = evaluation.get("f1_score")
                self.model.roc_auc = evaluation.get("roc_auc")
                self.model.accuracy = evaluation.get("accuracy")
                update_fields += ["precision", "recall", "f1_score", "roc_auc", "accuracy"]
            elif self.model.model_type == "recommendation":
                self.model.precision = evaluation.get("precision")
                self.model.recall = evaluation.get("recall")
                self.model.f1_score = evaluation.get("f1")
                update_fields += ["precision", "recall", "f1_score"]

        self.model.save(update_fields=update_fields)

    def _save_model_if_supported(self, service: Any) -> None:
        """
        Sauvegarde le fichier modèle si le service implémente save().
        Ne lève jamais d'exception — un échec de sauvegarde est non bloquant.
        """
        if not callable(getattr(service, "save", None)):
            return

        try:
            dir_path = f"/tmp/ml_models/{self.model.id}/"
            os.makedirs(dir_path, exist_ok=True)
            filename = f"model_v{self.model.version}.joblib"
            model_path = os.path.join(dir_path, filename)

            service.save(model_path)

            with open(model_path, "rb") as f:
                self.model.model_file.save(filename, ContentFile(f.read()), save=False)
            self.model.save(update_fields=["model_file", "updated_at"])

            os.remove(model_path)
            logger.info("Modèle '%s' sauvegardé : %s", self.model.name, filename)
        except Exception as exc:
            logger.warning(
                "Sauvegarde du fichier modèle impossible pour '%s' : %s",
                self.model.name, exc,
            )

    def _save_anomalies(self, anomalies: list[dict]) -> list[Anomaly]:
        """Persiste les anomalies détectées et notifie pour les niveaux high/critical."""
        saved = []
        for a in anomalies:
            try:
                expected = a.get("expected", a["value"])
                obj = Anomaly.objects.create(
                    model=self.model,
                    dimensional_schema=self.model.dimensional_schema,
                    measure=self.model.measure,
                    date=a["date"],
                    value=float(a["value"]),
                    expected_value=float(expected),
                    deviation=float(a["value"]) - float(expected),
                    deviation_percentage=abs(float(a.get("score", 0)) * 100),
                    severity=a.get("severity", "medium"),
                )
                saved.append(obj)
                if obj.severity in ("high", "critical"):
                    self._notify_anomaly(obj)
            except Exception as exc:
                logger.warning("Impossible de persister l'anomalie : %s", exc)
        return saved

    def _save_recommendations(self, recommendations: list) -> list[Recommendation]:
        """Persiste les recommandations générées."""
        saved = []
        NULL_UUID = "00000000-0000-0000-0000-000000000000"
        for rec in recommendations:
            try:
                obj = Recommendation.objects.create(
                    model=self.model,
                    recommendation_type="insight",
                    target_id=rec.get("id", NULL_UUID),
                    title=rec.get("title", "Recommandation"),
                    description=rec.get("description", ""),
                    confidence=min(float(rec.get("score", 0.5)) * 100, 100.0),
                    priority="medium",
                    score=rec.get("score", 0.5),
                )
                saved.append(obj)
            except Exception as exc:
                logger.warning("Impossible de persister la recommandation : %s", exc)
        return saved

    def _notify(self, event: str, error: Optional[str] = None) -> None:
        """Envoie une notification de fin d'entraînement (succès ou échec)."""
        try:
            svc = NotificationService()
            if event == "training_completed":
                title = f"🤖 Modèle entraîné : {self.model.name}"
                msg = (
                    f"Le modèle {self.model.name} a été entraîné avec succès "
                    f"(v{self.model.version}, {self.model.training_duration_ms:.0f}ms)."
                )
                if self.model.accuracy:
                    msg += f" Précision : {self.model.accuracy:.2f}%."
                priority = "medium"
            else:
                title = f"❌ Entraînement échoué : {self.model.name}"
                msg = f"Le modèle {self.model.name} a échoué. Erreur : {error}"
                priority = "high"

            svc.create_notification(
                recipient=self.model.owner,
                notification_type="system_alert",
                title=title,
                message=msg,
                priority=priority,
            )
        except Exception as exc:
            logger.error("Erreur de notification d'entraînement : %s", exc)

    def _notify_anomaly(self, anomaly: Anomaly) -> None:
        """Envoie une notification pour une anomalie de niveau high ou critical."""
        try:
            svc = NotificationService()
            svc.create_notification(
                recipient=self.model.owner,
                notification_type="anomaly_detected",
                title=f"🔍 Anomalie {anomaly.severity.upper()} — {self.model.name}",
                message=(
                    f"Anomalie {anomaly.get_severity_display()} détectée le {anomaly.date}. "
                    f"Valeur : {anomaly.value:.2f} | "
                    f"Attendue : {anomaly.expected_value:.2f} | "
                    f"Écart : {anomaly.deviation_percentage:.1f}%"
                ),
                priority="critical" if anomaly.severity == "critical" else "high",
                metadata={
                    "anomaly_id": str(anomaly.id),
                    "severity": anomaly.severity,
                    "model_id": str(self.model.id),
                },
            )
        except Exception as exc:
            logger.error("Erreur de notification d'anomalie : %s", exc)
