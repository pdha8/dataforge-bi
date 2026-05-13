# apps/visualizations/filters.py
"""
Filtres pour l'application visualizations
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, Count

from .models import Dashboard, Widget, KPI, Report, VisualizationActivity
from .constants import (
    DASHBOARD_TYPES, STATUS_CHOICES, ACCESS_LEVELS,
    WIDGET_TYPES, KPI_TYPES, EXPORT_FORMATS
)


class DashboardFilter(filters.FilterSet):
    """Filtres pour Dashboard"""
    
    # Filtres texte
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    category = filters.CharFilter(lookup_expr='icontains', label="Catégorie")
    
    # Filtres choix
    dashboard_type = filters.ChoiceFilter(choices=DASHBOARD_TYPES, label="Type")
    status = filters.ChoiceFilter(choices=STATUS_CHOICES, label="Statut")
    access_level = filters.ChoiceFilter(choices=ACCESS_LEVELS, label="Accès")
    
    # Filtres booléens
    is_published = filters.BooleanFilter(method='filter_is_published', label="Publié")
    has_widgets = filters.BooleanFilter(method='filter_has_widgets', label="A des widgets")
    
    # Filtres numériques
    min_views = filters.NumberFilter(field_name='view_count', lookup_expr='gte', label="Vues min")
    max_views = filters.NumberFilter(field_name='view_count', lookup_expr='lte', label="Vues max")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    last_viewed_after = filters.DateTimeFilter(field_name='last_viewed', lookup_expr='gte', label="Vu après")
    
    # Filtres relations
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    team = filters.UUIDFilter(field_name='team__id', label="ID équipe")
    
    # Recherche générale
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = Dashboard
        fields = ['dashboard_type', 'status', 'access_level', 'owner', 'team']
    
    def filter_is_published(self, queryset, name, value):
        if value:
            return queryset.filter(status='published')
        return queryset.exclude(status='published')
    
    def filter_has_widgets(self, queryset, name, value):
        if value:
            return queryset.annotate(widget_count=Count('widgets')).filter(widget_count__gt=0)
        return queryset.annotate(widget_count=Count('widgets')).filter(widget_count=0)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(category__icontains=value)
        )


class WidgetFilter(filters.FilterSet):
    """Filtres pour Widget"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    widget_type = filters.ChoiceFilter(choices=WIDGET_TYPES, label="Type")
    dashboard = filters.UUIDFilter(field_name='dashboard__id', label="ID tableau de bord")
    dimensional_schema = filters.UUIDFilter(field_name='dimensional_schema__id', label="ID schéma")
    is_enabled = filters.BooleanFilter(label="Activé")
    cache_enabled = filters.BooleanFilter(label="Cache activé")
    
    class Meta:
        model = Widget
        fields = ['widget_type', 'dashboard', 'dimensional_schema', 'is_enabled', 'cache_enabled']


class KPIFilter(filters.FilterSet):
    """Filtres pour KPI"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    kpi_type = filters.ChoiceFilter(choices=KPI_TYPES, label="Type")
    dimensional_schema = filters.UUIDFilter(field_name='dimensional_schema__id', label="ID schéma")
    dashboard = filters.UUIDFilter(field_name='dashboard__id', label="ID tableau de bord")
    is_active = filters.BooleanFilter(label="Actif")
    track_trend = filters.BooleanFilter(label="Suivi tendance")
    
    min_value = filters.NumberFilter(field_name='current_value', lookup_expr='gte', label="Valeur min")
    max_value = filters.NumberFilter(field_name='current_value', lookup_expr='lte', label="Valeur max")
    
    status = filters.ChoiceFilter(
        choices=[('success', 'Succès'), ('warning', 'Alerte'), ('critical', 'Critique')],
        method='filter_status',
        label="Statut"
    )
    
    class Meta:
        model = KPI
        fields = ['kpi_type', 'dimensional_schema', 'dashboard', 'is_active', 'track_trend']
    
    def filter_status(self, queryset, name, value):
        if value == 'success':
            ids = [k.id for k in queryset if k.get_status() == 'success']
            return queryset.filter(id__in=ids)
        elif value == 'warning':
            ids = [k.id for k in queryset if k.get_status() == 'warning']
            return queryset.filter(id__in=ids)
        elif value == 'critical':
            ids = [k.id for k in queryset if k.get_status() == 'critical']
            return queryset.filter(id__in=ids)
        return queryset


class ReportFilter(filters.FilterSet):
    """Filtres pour Report"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    format = filters.ChoiceFilter(choices=EXPORT_FORMATS, label="Format")
    dashboard = filters.UUIDFilter(field_name='dashboard__id', label="ID tableau de bord")
    is_active = filters.BooleanFilter(label="Actif")
    has_schedule = filters.BooleanFilter(method='filter_has_schedule', label="Planifié")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    last_generated_after = filters.DateTimeFilter(field_name='last_generated', lookup_expr='gte', label="Généré après")
    
    class Meta:
        model = Report
        fields = ['format', 'dashboard', 'is_active']
    
    def filter_has_schedule(self, queryset, name, value):
        if value:
            return queryset.filter(schedule__isnull=False, schedule__gt='')
        return queryset.filter(Q(schedule__isnull=True) | Q(schedule=''))


class ActivityFilter(filters.FilterSet):
    """Filtres pour VisualizationActivity"""
    
    user = filters.UUIDFilter(field_name='user__id', label="ID utilisateur")
    dashboard = filters.UUIDFilter(field_name='dashboard__id', label="ID tableau de bord")
    activity_type = filters.ChoiceFilter(choices=VisualizationActivity.ACTIVITY_TYPES, label="Type")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Avant")
    
    class Meta:
        model = VisualizationActivity
        fields = ['user', 'dashboard', 'activity_type']