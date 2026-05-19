# apps/data_sources/urls.py - METTRE À JOUR

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('sources', views.DataSourceViewSet, basename='datasource')
router.register('tables', views.DataTableViewSet, basename='datatable')
router.register('queries', views.DataQueryViewSet, basename='dataquery')
router.register('star-schemas', views.StarSchemaViewSet, basename='starschema')
router.register('logs', views.DataSourceLogViewSet, basename='datasourcelog')
router.register('metrics', views.DataSourceMetricViewSet, basename='datasourcemetric')
router.register('files', views.DataSourceFileViewSet, basename='datasourcefile')           # ← AJOUTER
router.register('power-queries', views.PowerQueryViewSet, basename='powerquery')           # ← AJOUTER
router.register('connections', views.DataSourceConnectionViewSet, basename='datasourceconnection')  # ← AJOUTER

urlpatterns = router.urls