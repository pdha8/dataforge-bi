# apps/notifications/urls.py
"""
URLs pour l'application notifications
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'channels', views.NotificationChannelViewSet, basename='channel')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'alerts', views.AlertRuleViewSet, basename='alert-rule')

urlpatterns = router.urls