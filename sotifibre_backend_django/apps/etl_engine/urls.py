# apps/etl_engine/urls.py
"""
URLs pour l'application etl_engine
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('pipelines', views.ETLPipelineViewSet, basename='etlpipeline')
router.register('transformations', views.TransformationViewSet, basename='transformation')
router.register('executions', views.ExecutionLogViewSet, basename='executionlog')
router.register('target-schemas', views.TargetSchemaViewSet, basename='targetschema')
router.register('source-schemas', views.SourceSchemaViewSet, basename='sourceschema')
router.register('notifications', views.PipelineNotificationViewSet, basename='pipelinenotification')

urlpatterns = router.urls