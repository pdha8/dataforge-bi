# apps/etl_engine/filters.py
"""
Filtres pour l'application etl_engine
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, Count

from .models import ETLPipeline, Transformation, ExecutionLog
from .constants import (
    PIPELINE_TYPES, 
    PIPELINE_STATUS, 
    EXECUTION_STATUS, 
    PROCESSING_MODES,
    ERROR_STRATEGIES,
    TRANSFORMATION_TYPES,
    TRIGGERED_BY_CHOICES  # ← AJOUTER
)


class ETLPipelineFilter(filters.FilterSet):
    """Filtres pour ETLPipeline"""
    
    # Filtres texte
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    category = filters.CharFilter(lookup_expr='icontains', label="Catégorie")
    tags = filters.CharFilter(method='filter_tags', label="Tags")
    
    # Filtres choix
    pipeline_type = filters.ChoiceFilter(choices=PIPELINE_TYPES, label="Type de pipeline")
    status = filters.ChoiceFilter(choices=PIPELINE_STATUS, label="Statut")
    error_strategy = filters.ChoiceFilter(choices=ERROR_STRATEGIES, label="Stratégie d'erreur")
    processing_mode = filters.ChoiceFilter(choices=PROCESSING_MODES, label="Mode de traitement")
    
    # Filtres booléens
    schedule_enabled = filters.BooleanFilter(label="Planification activée")
    notifications_enabled = filters.BooleanFilter(label="Notifications activées")
    is_active = filters.BooleanFilter(method='filter_is_active', label="Actif")
    
    # Filtres numériques
    min_priority = filters.NumberFilter(field_name='priority', lookup_expr='lte', label="Priorité max")
    max_priority = filters.NumberFilter(field_name='priority', lookup_expr='gte', label="Priorité min")
    min_success_rate = filters.NumberFilter(method='filter_min_success_rate', label="Taux succès min")
    min_quality_score = filters.NumberFilter(field_name='data_quality_score', lookup_expr='gte', label="Score qualité min")
    
    # Filtres de dates
    last_execution_after = filters.DateTimeFilter(field_name='last_execution', lookup_expr='gte', label="Dernière exécution après")
    last_execution_before = filters.DateTimeFilter(field_name='last_execution', lookup_expr='lte', label="Dernière exécution avant")
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    # Filtres relations
    source = filters.UUIDFilter(field_name='source__id', label="ID source")
    target = filters.UUIDFilter(field_name='target__id', label="ID cible")
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    team = filters.UUIDFilter(field_name='team__id', label="ID équipe")
    
    # Filtres de santé
    health_status = filters.ChoiceFilter(
        choices=[('critical', 'Critique'), ('warning', 'Alerte'), ('poor', 'Médiocre'), ('fair', 'Moyen'), ('good', 'Bon')],
        method='filter_health_status',
        label="État de santé"
    )
    
    # Recherche générale
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = ETLPipeline
        fields = ['pipeline_type', 'status', 'error_strategy', 'processing_mode']
    
    def filter_tags(self, queryset, name, value):
        """Filtre par tags"""
        tags = [t.strip() for t in value.split(',') if t.strip()]
        for tag in tags:
            queryset = queryset.filter(tags__contains=[tag])
        return queryset
    
    def filter_is_active(self, queryset, name, value):
        """Filtre les pipelines actifs"""
        if value:
            return queryset.filter(status='active')
        return queryset.exclude(status='active')
    
    def filter_min_success_rate(self, queryset, name, value):
        """Filtre par taux de succès minimum"""
        result_ids = []
        for pipeline in queryset:
            if pipeline.success_rate >= value:
                result_ids.append(pipeline.id)
        return queryset.filter(id__in=result_ids)
    
    def filter_health_status(self, queryset, name, value):
        """Filtre par état de santé"""
        result_ids = []
        for pipeline in queryset:
            if pipeline.health_status == value:
                result_ids.append(pipeline.id)
        return queryset.filter(id__in=result_ids)
    
    def filter_search(self, queryset, name, value):
        """Recherche multi-champs"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(category__icontains=value)
        )


class TransformationFilter(filters.FilterSet):
    """Filtres pour Transformation"""
    
    pipeline = filters.UUIDFilter(field_name='pipeline__id', label="ID pipeline")
    pipeline_name = filters.CharFilter(field_name='pipeline__name', lookup_expr='icontains', label="Nom pipeline")
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    transformation_type = filters.ChoiceFilter(choices=TRANSFORMATION_TYPES, label="Type")
    
    is_enabled = filters.BooleanFilter(label="Activée")
    is_critical = filters.BooleanFilter(label="Critique")
    
    min_execution_count = filters.NumberFilter(field_name='execution_count', lookup_expr='gte', label="Exécutions min")
    min_avg_duration = filters.NumberFilter(field_name='avg_duration_ms', lookup_expr='gte', label="Durée moyenne min (ms)")
    
    class Meta:
        model = Transformation
        fields = ['pipeline', 'transformation_type', 'is_enabled', 'is_critical']


class ExecutionLogFilter(filters.FilterSet):
    """Filtres pour ExecutionLog"""
    
    pipeline = filters.UUIDFilter(field_name='pipeline__id', label="ID pipeline")
    pipeline_name = filters.CharFilter(field_name='pipeline__name', lookup_expr='icontains', label="Nom pipeline")
    status = filters.ChoiceFilter(choices=EXECUTION_STATUS, label="Statut")
    triggered_by = filters.ChoiceFilter(choices=TRIGGERED_BY_CHOICES, label="Déclenché par")  # ← CORRIGÉ
    
    started_after = filters.DateTimeFilter(field_name='started_at', lookup_expr='gte', label="Début après")
    started_before = filters.DateTimeFilter(field_name='started_at', lookup_expr='lte', label="Début avant")
    
    min_duration = filters.NumberFilter(field_name='duration_seconds', lookup_expr='gte', label="Durée min (s)")
    max_duration = filters.NumberFilter(field_name='duration_seconds', lookup_expr='lte', label="Durée max (s)")
    
    min_rows_processed = filters.NumberFilter(field_name='rows_read', lookup_expr='gte', label="Lignes lues min")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = ExecutionLog
        fields = ['pipeline', 'status', 'triggered_by']
    
    def filter_search(self, queryset, name, value):
        """Recherche dans l'ID d'exécution et les messages d'erreur"""
        return queryset.filter(
            Q(execution_id__icontains=value) |
            Q(error_message__icontains=value)
        )