"""
apps/ml_analytics/views.py

ViewSets DRF pour l'application ML Analytics.
"""
from __future__ import annotations

import logging

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.pagination import StandardPagination
from apps.core.permissions import CanManageDataSources, CanViewDataSources
from apps.core.responses import created_response, error_response, success_response

from .filters import (
    AnomalyFilter,
    ForecastFilter,
    MLModelFilter,
    ModelTrainingLogFilter,
    RecommendationFilter,
)
from .models import (
    Anomaly,
    Forecast,
    MLModel,
    ModelTrainingLog,
    Recommendation,
    SegmentationResult,
)
from .serializers import (
    AnomalySerializer,
    ForecastSerializer,
    MLModelCreateSerializer,
    MLModelDetailSerializer,
    MLModelPredictSerializer,
    MLModelSerializer,
    ModelTrainingLogSerializer,
    RecommendationSerializer,
    SegmentationResultSerializer,
)
from .services import MLService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MLModel
# ─────────────────────────────────────────────────────────────────────────────

class MLModelViewSet(viewsets.ModelViewSet):
    queryset = MLModel.objects.all().select_related(
        "dimensional_schema", "measure", "owner", "team"
    )
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MLModelFilter
    search_fields = ["name", "description", "tags"]
    ordering_fields = ["name", "created_at", "accuracy", "last_trained", "version"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MLModelDetailSerializer
        if self.action == "create":
            return MLModelCreateSerializer
        return MLModelSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(
            MLModelSerializer(serializer.instance, context=self.get_serializer_context()).data,
            "Modèle ML créé avec succès"
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ── Actions personnalisées ─────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def train(self, request, pk=None):
        """Lance l'entraînement du modèle."""
        model = self.get_object()
        service = MLService(model)
        result = service.train()
        if result["success"]:
            return success_response(
                {
                    "model_id": str(model.id),
                    "version": model.version,
                    "duration_ms": result.get("duration_ms"),
                    "performance": model.get_performance_summary(),
                },
                "Modèle entraîné avec succès.",
            )
        return error_response(
            result.get("error", "Erreur inconnue."),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=True, methods=["post"])
    def predict(self, request, pk=None):
        """Effectue une prédiction avec le modèle."""
        model = self.get_object()
        serializer = MLModelPredictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = MLService(model)
        result = service.predict(serializer.validated_data)
        if result["success"]:
            return success_response(result, "Prédiction effectuée avec succès.")
        return error_response(
            result.get("error", "Erreur de prédiction."),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=True, methods=["post"])
    def deploy(self, request, pk=None):
        """Déploie un modèle entraîné."""
        model = self.get_object()
        if not model.is_ready():
            return error_response(
                "Le modèle doit être entraîné avant d'être déployé.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        model.status = "deployed"
        model.save(update_fields=["status", "updated_at"])
        return success_response({"status": "deployed"}, "Modèle déployé avec succès.")

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive un modèle."""
        model = self.get_object()
        model.status = "archived"
        model.is_active = False
        model.save(update_fields=["status", "is_active", "updated_at"])
        return success_response({"status": "archived"}, "Modèle archivé.")

    @action(detail=True, methods=["get"])
    def training_logs(self, request, pk=None):
        """Retourne les logs d'entraînement du modèle."""
        model = self.get_object()
        logs = model.training_logs.all()
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = ModelTrainingLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ModelTrainingLogSerializer(logs, many=True)
        return success_response(serializer.data, "Logs d'entraînement récupérés.")

    @action(detail=True, methods=["get"])
    def forecasts(self, request, pk=None):
        """Retourne les prévisions du modèle."""
        model = self.get_object()
        forecasts = model.forecasts.all()
        page = self.paginate_queryset(forecasts)
        if page is not None:
            serializer = ForecastSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ForecastSerializer(forecasts, many=True)
        return success_response(serializer.data, "Prévisions récupérées.")

    @action(detail=True, methods=["get"])
    def anomalies(self, request, pk=None):
        """Retourne les anomalies détectées par le modèle."""
        model = self.get_object()
        qs = model.anomalies.all()
        if severity := request.query_params.get("severity"):
            qs = qs.filter(severity=severity)
        if request.query_params.get("unresolved") == "true":
            qs = qs.filter(is_resolved=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(AnomalySerializer(page, many=True).data)
        return success_response(AnomalySerializer(qs, many=True).data, "Anomalies récupérées.")

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        """Retourne les recommandations actives du modèle."""
        model = self.get_object()
        qs = model.recommendations.filter(is_applied=False, is_dismissed=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(RecommendationSerializer(page, many=True).data)
        return success_response(
            RecommendationSerializer(qs, many=True).data, "Recommandations récupérées."
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Statistiques globales sur tous les modèles."""
        qs = self.get_queryset()
        stats = {
            "total": qs.count(),
            "active": qs.filter(is_active=True).count(),
            "by_type": dict(qs.values_list("model_type").annotate(count=Count("id"))),
            "by_status": dict(qs.values_list("status").annotate(count=Count("id"))),
            "avg_accuracy": round(
                qs.aggregate(v=Avg("accuracy"))["v"] or 0, 2
            ),
        }
        return success_response(stats, "Statistiques récupérées.")


# ─────────────────────────────────────────────────────────────────────────────
# Forecast
# ─────────────────────────────────────────────────────────────────────────────

class ForecastViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Forecast.objects.all().select_related("model", "used_by")
    serializer_class = ForecastSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ForecastFilter
    ordering_fields = ["forecast_date", "generated_at", "accuracy"]
    ordering = ["-forecast_date"]

    @action(detail=True, methods=["get"])
    def chart(self, request, pk=None):
        """Données de graphique pour la prévision."""
        forecast = self.get_object()
        return success_response(
            {"chart_data": forecast.get_chart_data(), "summary": forecast.get_summary()},
            "Données de graphique récupérées.",
        )

    @action(detail=True, methods=["post"])
    def mark_used(self, request, pk=None):
        """Marque la prévision comme utilisée."""
        forecast = self.get_object()
        forecast.is_used = True
        forecast.used_by = request.user
        forecast.save(update_fields=["is_used", "used_by"])
        return success_response(None, "Prévision marquée comme utilisée.")


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly
# ─────────────────────────────────────────────────────────────────────────────

class AnomalyViewSet(viewsets.ModelViewSet):
    queryset = Anomaly.objects.all().select_related(
        "model", "dimensional_schema", "measure", "resolved_by"
    )
    serializer_class = AnomalySerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AnomalyFilter
    ordering_fields = ["detected_at", "date", "severity", "deviation_percentage"]
    ordering = ["-detected_at"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), CanManageDataSources()]
        return [IsAuthenticated(), CanViewDataSources()]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        anomaly = self.get_object()
        anomaly.confirm()
        return success_response(None, "Anomalie confirmée.")

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        anomaly = self.get_object()
        notes = request.data.get("notes", "")
        anomaly.resolve(request.user, notes)
        return success_response(None, "Anomalie résolue.")

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        last_30d = timezone.now() - timezone.timedelta(days=30)
        stats = {
            "total": qs.count(),
            "last_30d": qs.filter(detected_at__gte=last_30d).count(),
            "unresolved": qs.filter(is_resolved=False).count(),
            "by_severity": dict(
                qs.values_list("severity").annotate(count=Count("id"))
            ),
            "confirmed": qs.filter(is_confirmed=True).count(),
            "resolved": qs.filter(is_resolved=True).count(),
        }
        return success_response(stats, "Statistiques des anomalies récupérées.")


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all().select_related("model", "applied_by")
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RecommendationFilter
    search_fields = ["title", "description"]
    ordering_fields = ["confidence", "created_at", "priority"]
    ordering = ["-confidence"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), CanManageDataSources()]
        return [IsAuthenticated(), CanViewDataSources()]

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.apply(request.user)
        return success_response(None, "Recommandation appliquée.")

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.dismiss()
        return success_response(None, "Recommandation ignorée.")

    @action(detail=False, methods=["get"])
    def active(self, request):
        qs = self.get_queryset().filter(is_applied=False, is_dismissed=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(
            self.get_serializer(qs, many=True).data, "Recommandations actives récupérées."
        )


# ─────────────────────────────────────────────────────────────────────────────
# SegmentationResult
# ─────────────────────────────────────────────────────────────────────────────

class SegmentationResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SegmentationResult.objects.all().select_related("model")
    serializer_class = SegmentationResultSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["percentage", "size"]
    ordering = ["-percentage"]


# ─────────────────────────────────────────────────────────────────────────────
# ModelTrainingLog
# ─────────────────────────────────────────────────────────────────────────────

class ModelTrainingLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModelTrainingLog.objects.all().select_related("model")
    serializer_class = ModelTrainingLogSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ModelTrainingLogFilter
    ordering_fields = ["started_at", "duration_ms"]
    ordering = ["-started_at"]
