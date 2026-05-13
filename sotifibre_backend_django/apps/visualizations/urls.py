# apps/visualizations/urls.py
"""
URLs pour l'application visualizations
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'dashboards', views.DashboardViewSet, basename='dashboard')
router.register(r'widgets', views.WidgetViewSet, basename='widget')
router.register(r'kpis', views.KPIViewSet, basename='kpi')
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'favorites', views.FavoriteViewSet, basename='favorite')
router.register(r'activities', views.VisualizationActivityViewSet, basename='activity')

urlpatterns = router.urls