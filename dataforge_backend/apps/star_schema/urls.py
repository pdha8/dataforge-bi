# apps/star_schema/urls.py
"""
URLs pour l'application star_schema
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'dimensional-schemas', views.DimensionalSchemaViewSet, basename='dimensional-schema')  # ← Renommé
router.register(r'fact-relationships', views.FactRelationshipViewSet, basename='fact-relationship')
router.register(r'dimension-hierarchies', views.DimensionHierarchyViewSet, basename='dimension-hierarchy')
router.register(r'calculations', views.CustomCalculationViewSet, basename='calculation')
router.register(r'custom-calculations', views.CustomCalculationViewSet, basename='custom-calculation')
router.register(r'galaxies', views.GalaxySchemaViewSet, basename='galaxy')
router.register(r'galaxy-schemas', views.GalaxySchemaViewSet, basename='galaxy-schema')

urlpatterns = router.urls