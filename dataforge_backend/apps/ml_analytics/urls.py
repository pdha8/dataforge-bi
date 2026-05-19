"""
apps/ml_analytics/urls.py
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"models",          views.MLModelViewSet,           basename="ml-model")
router.register(r"forecasts",       views.ForecastViewSet,          basename="forecast")
router.register(r"anomalies",       views.AnomalyViewSet,           basename="anomaly")
router.register(r"segmentations",   views.SegmentationResultViewSet, basename="segmentation")
router.register(r"recommendations", views.RecommendationViewSet,    basename="recommendation")
router.register(r"training-logs",   views.ModelTrainingLogViewSet,  basename="training-log")

urlpatterns = [
    path("", include(router.urls)),
]
