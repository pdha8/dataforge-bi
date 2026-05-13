# apps/notifications/views.py
"""
Vues pour l'application notifications
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.utils import timezone

from apps.core.permissions import CanManageDataSources, CanViewDataSources
from apps.core.responses import success_response, error_response, created_response
from apps.core.pagination import StandardPagination

from .models import Notification, NotificationChannel, Subscription, AlertRule
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    NotificationChannelSerializer, SubscriptionSerializer,
    AlertRuleSerializer, AlertRuleCreateSerializer,
    NotificationStatsSerializer
)
from .filters import NotificationFilter, NotificationChannelFilter, SubscriptionFilter, AlertRuleFilter
from .services import NotificationService, AlertRuleService


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour Notification
    Gère les notifications utilisateur
    """
    
    queryset = Notification.objects.all().select_related('recipient', 'dashboard', 'kpi', 'report', 'pipeline')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationFilter
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtre les notifications selon l'utilisateur
        Les admins voient tout, les autres voient leurs notifications
        """
        user = self.request.user
        if user.is_superuser or user.is_admin:
            return Notification.objects.all()
        return Notification.objects.filter(recipient=user)
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action"""
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    def get_permissions(self):
        """
        Définit les permissions selon l'action
        La création/modification/suppression nécessite des droits admin
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Crée une notification et l'envoie immédiatement"""
        notification = serializer.save()
        service = NotificationService()
        for channel in notification.channels:
            service.send(notification, channel)
        return notification
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Marque une notification comme lue
        POST /api/notifications/notifications/{id}/mark_read/
        """
        notification = self.get_object()
        service = NotificationService()
        notification = service.mark_as_read(notification.id, request.user)
        
        return success_response(
            NotificationSerializer(notification).data,
            "Notification marquée comme lue"
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Marque toutes les notifications comme lues
        POST /api/notifications/notifications/mark_all_read/
        """
        notifications = self.get_queryset().filter(read_at__isnull=True)
        count = notifications.update(read_at=timezone.now(), status='read')
        
        return success_response(
            {'count': count},
            f"{count} notification(s) marquée(s) comme lue(s)"
        )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Récupère le nombre de notifications non lues
        GET /api/notifications/notifications/unread_count/
        """
        count = self.get_queryset().filter(read_at__isnull=True).count()
        
        return success_response(
            {'count': count},
            "Nombre de notifications non lues"
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques des notifications
        GET /api/notifications/notifications/stats/
        """
        stats = Notification.objects.stats(request.user)
        
        return success_response(stats, "Statistiques récupérées")


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour NotificationChannel
    Gère les canaux de notification des utilisateurs (email, SMS, Slack, etc.)
    """
    
    queryset = NotificationChannel.objects.all().select_related('user')
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationChannelFilter
    search_fields = ['address']
    ordering_fields = ['channel', 'created_at']
    ordering = ['user', 'channel']
    
    def get_queryset(self):
        """
        Filtre les canaux selon l'utilisateur
        Les admins voient tout, les autres voient leurs propres canaux
        """
        user = self.request.user
        if user.is_superuser or user.is_admin:
            return NotificationChannel.objects.all()
        return NotificationChannel.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Crée un canal et génère un token de vérification"""
        instance = serializer.save(user=self.request.user)
        instance.generate_verification_token()
        return instance
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Vérifie un canal de notification avec un token
        POST /api/notifications/channels/{id}/verify/
        """
        channel = self.get_object()
        token = request.data.get('token')
        
        if channel.verify(token):
            return success_response(None, "Canal vérifié avec succès")
        else:
            return error_response("Token invalide", status_code=400)
    
    @action(detail=True, methods=['post'])
    def resend_verification(self, request, pk=None):
        """
        Renvoie un token de vérification par email
        POST /api/notifications/channels/{id}/resend_verification/
        """
        channel = self.get_object()
        token = channel.generate_verification_token()
        
        # Envoyer le token par email
        from django.core.mail import send_mail
        from django.conf import settings
        
        send_mail(
            subject="Vérification de votre canal",
            message=f"Votre token de vérification: {token}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[channel.user.email],
            fail_silently=False,
        )
        
        return success_response(None, "Token de vérification envoyé")


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour Subscription
    Gère les abonnements des utilisateurs aux types de notifications
    """
    
    queryset = Subscription.objects.all().select_related('user')
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubscriptionFilter
    search_fields = ['filters']
    ordering_fields = ['notification_type', 'created_at']
    ordering = ['user', 'notification_type']
    
    def get_queryset(self):
        """
        Filtre les abonnements selon l'utilisateur
        Les admins voient tout, les autres voient leurs propres abonnements
        """
        user = self.request.user
        if user.is_superuser or user.is_admin:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Crée un abonnement pour l'utilisateur connecté"""
        return serializer.save(user=self.request.user)


class AlertRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour AlertRule
    Gère les règles d'alerte pour les KPIs
    """
    
    queryset = AlertRule.objects.all().select_related('kpi')
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlertRuleFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'trigger_count', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action"""
        if self.action == 'create':
            return AlertRuleCreateSerializer
        return AlertRuleSerializer
    
    def perform_create(self, serializer):
        """Crée une règle d'alerte"""
        return serializer.save()
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Teste une règle d'alerte avec des valeurs simulées
        POST /api/notifications/alerts/{id}/test/
        """
        rule = self.get_object()
        
        # Récupérer les valeurs de test
        current_value = request.data.get('current_value', 100)
        previous_value = request.data.get('previous_value', 80)
        
        # Évaluer la règle
        triggered = rule.evaluate(float(current_value), float(previous_value) if previous_value else None)
        
        return success_response(
            {'triggered': triggered},
            "Règle testée"
        )
    
    @action(detail=False, methods=['post'])
    def check_all(self, request):
        """
        Vérifie toutes les règles d'alerte actives
        POST /api/notifications/alerts/check_all/
        """
        service = AlertRuleService()
        service.check_all_rules()
        
        return success_response(None, "Vérification des règles lancée")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques des règles d'alerte
        GET /api/notifications/alerts/stats/
        """
        total = AlertRule.objects.count()
        active = AlertRule.objects.filter(is_enabled=True).count()
        triggered_today = AlertRule.objects.filter(
            last_triggered__date=timezone.now().date()
        ).count()
        
        by_condition = dict(
            AlertRule.objects.values_list('condition').annotate(count=Count('id'))
        )
        
        stats = {
            'total': total,
            'active': active,
            'triggered_today': triggered_today,
            'by_condition': by_condition,
        }
        
        return success_response(stats, "Statistiques récupérées")