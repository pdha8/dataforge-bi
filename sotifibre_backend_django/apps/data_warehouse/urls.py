# apps/data_warehouse/urls.py
"""
URLs pour l'application data_warehouse
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('schemas', views.DataWarehouseSchemaViewSet, basename='dwschema')
router.register('tables', views.DataWarehouseTableViewSet, basename='dwtable')
router.register('fact-tables', views.FactTableViewSet, basename='facttable')
router.register('dimension-tables', views.DimensionTableViewSet, basename='dimensiontable')
router.register('star-schemas', views.StarSchemaViewSet, basename='starschema')
router.register('measures', views.MeasureViewSet, basename='measure')
router.register('attributes', views.DimensionAttributeViewSet, basename='attribute')
router.register('aggregations', views.AggregationTableViewSet, basename='aggregation')
router.register('logs', views.DataWarehouseLogViewSet, basename='dwlog')
router.register('metrics', views.DataWarehouseMetricViewSet, basename='dwmetric')

urlpatterns = router.urls