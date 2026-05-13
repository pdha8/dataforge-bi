# apps/notifications/filters.py
"""
Filtres pour l'application notifications
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q

from .models import Notification, NotificationChannel, Subscription, AlertRule
from .constants import NOTIFICATION_TYPES, CHANNELS, NOTIFICATION_STATUS, PRIORITIES


class NotificationFilter(filters.FilterSet):
    """Filtres pour Notification"""
    
    # Filtres texte
    title = filters.CharFilter(lookup_expr='icontains', label="Titre")
    message = filters.CharFilter(lookup_expr='icontains', label="Message")
    
    # Filtres choix
    notification_type = filters.ChoiceFilter(choices=NOTIFICATION_TYPES, label="Type")
    status = filters.ChoiceFilter(choices=NOTIFICATION_STATUS, label="Statut")
    priority = filters.ChoiceFilter(choices=PRIORITIES, label="Priorité")
    
    # Filtres booléens
    is_read = filters.BooleanFilter(method='filter_is_read', label="Lu")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    sent_after = filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte', label="Envoyé après")
    
    # Filtres relations
    recipient = filters.UUIDFilter(field_name='recipient__id', label="ID destinataire")
    dashboard = filters.UUIDFilter(field_name='dashboard__id', label="ID dashboard")
    kpi = filters.UUIDFilter(field_name='kpi__id', label="ID KPI")
    report = filters.UUIDFilter(field_name='report__id', label="ID rapport")
    
    # Recherche générale
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = Notification
        fields = ['notification_type', 'status', 'priority', 'recipient']
    
    def filter_is_read(self, queryset, name, value):
        if value:
            return queryset.filter(read_at__isnull=False)
        return queryset.filter(read_at__isnull=True)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(message__icontains=value)
        )


class NotificationChannelFilter(filters.FilterSet):
    """Filtres pour NotificationChannel"""
    
    channel = filters.ChoiceFilter(choices=CHANNELS, label="Canal")
    is_enabled = filters.BooleanFilter(label="Activé")
    is_verified = filters.BooleanFilter(label="Vérifié")
    user = filters.UUIDFilter(field_name='user__id', label="ID utilisateur")
    
    class Meta:
        model = NotificationChannel
        fields = ['channel', 'is_enabled', 'is_verified', 'user']


class SubscriptionFilter(filters.FilterSet):
    """Filtres pour Subscription"""
    
    notification_type = filters.ChoiceFilter(choices=NOTIFICATION_TYPES, label="Type")
    is_enabled = filters.BooleanFilter(label="Activé")
    user = filters.UUIDFilter(field_name='user__id', label="ID utilisateur")
    
    class Meta:
        model = Subscription
        fields = ['notification_type', 'is_enabled', 'user']


class AlertRuleFilter(filters.FilterSet):
    """Filtres pour AlertRule"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    condition = filters.ChoiceFilter(choices=AlertRule.CONDITION_CHOICES, label="Condition")
    is_enabled = filters.BooleanFilter(label="Activé")
    kpi = filters.UUIDFilter(field_name='kpi__id', label="ID KPI")
    
    min_trigger_count = filters.NumberFilter(field_name='trigger_count', lookup_expr='gte', label="Déclenchements min")
    max_trigger_count = filters.NumberFilter(field_name='trigger_count', lookup_expr='lte', label="Déclenchements max")
    
    last_triggered_after = filters.DateTimeFilter(field_name='last_triggered', lookup_expr='gte', label="Déclenché après")
    last_triggered_before = filters.DateTimeFilter(field_name='last_triggered', lookup_expr='lte', label="Déclenché avant")
    
    class Meta:
        model = AlertRule
        fields = ['condition', 'is_enabled', 'kpi']