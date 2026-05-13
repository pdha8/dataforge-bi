# apps/data_sources/filters.py
"""
Filtres pour l'application data_sources - Version optimisée
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, Count

from .models import DataSource, DataTable, DataQuery, DataSourceLog, DataSourceMetric, StarSchema
from .constants import (
    SOURCE_TYPE_CHOICES, 
    DATABASE_TYPES, 
    CONNECTION_STATUS, 
    REFRESH_CHOICES,
    QUERY_TYPES
)


class DataSourceFilter(filters.FilterSet):
    """Filtres avancés pour DataSource"""
    
    # Filtres texte
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    host = filters.CharFilter(lookup_expr='icontains', label="Hôte")
    database_name = filters.CharFilter(lookup_expr='icontains', label="Base de données")
    owner_team = filters.CharFilter(lookup_expr='icontains', label="Équipe propriétaire")
    category = filters.CharFilter(lookup_expr='icontains', label="Catégorie")
    tags = filters.CharFilter(method='filter_tags', label="Tags")
    
    # Filtres choix
    source_type = filters.ChoiceFilter(choices=SOURCE_TYPE_CHOICES, label="Type de source")
    database_type = filters.ChoiceFilter(choices=DATABASE_TYPES, label="Type de base")
    status = filters.ChoiceFilter(choices=CONNECTION_STATUS, label="Statut")
    sync_frequency = filters.ChoiceFilter(choices=REFRESH_CHOICES, label="Fréquence synchro")  # ← CORRIGÉ
    
    # Filtres booléens
    is_connected = filters.BooleanFilter(method='filter_is_connected', label="Connecté")
    has_errors = filters.BooleanFilter(method='filter_has_errors', label="A des erreurs")
    auto_refresh_enabled = filters.BooleanFilter(label="Auto rafraîchissement")
    is_validated = filters.BooleanFilter(label="Validé")
    is_public = filters.BooleanFilter(label="Public")
    
    # Filtres numériques
    min_success_rate = filters.NumberFilter(method='filter_min_success_rate', label="Taux succès min")
    min_quality_score = filters.NumberFilter(field_name='data_quality_score', lookup_expr='gte', label="Score qualité min")
    max_quality_score = filters.NumberFilter(field_name='data_quality_score', lookup_expr='lte', label="Score qualité max")
    min_consecutive_failures = filters.NumberFilter(field_name='consecutive_failures', lookup_expr='gte', label="Échecs consécutifs min")
    
    # Filtres de dates
    last_sync_after = filters.DateTimeFilter(field_name='last_sync', lookup_expr='gte', label="Dernière synchro après")
    last_sync_before = filters.DateTimeFilter(field_name='last_sync', lookup_expr='lte', label="Dernière synchro avant")
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    # Filtres relations
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    owner_email = filters.CharFilter(field_name='owner__email', lookup_expr='icontains', label="Email propriétaire")
    team = filters.UUIDFilter(field_name='team__id', label="ID équipe")
    created_by = filters.UUIDFilter(field_name='created_by__id', label="ID créateur")
    
    # Filtres de santé
    health_status = filters.ChoiceFilter(
        choices=[('critical', 'Critique'), ('warning', 'Alerte'), ('fair', 'Moyen'), ('good', 'Bon')],
        method='filter_health_status',
        label="État de santé"
    )
    
    # Recherche générale
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DataSource
        fields = ['source_type', 'database_type', 'status', 'sync_frequency']
    
    def filter_tags(self, queryset, name, value):
        """Filtre par tags"""
        tags = [t.strip() for t in value.split(',') if t.strip()]
        for tag in tags:
            queryset = queryset.filter(tags__contains=[tag])
        return queryset
    
    def filter_is_connected(self, queryset, name, value):
        """Filtre les sources connectées"""
        if value:
            return queryset.filter(status='active')
        return queryset.exclude(status='active')
    
    def filter_has_errors(self, queryset, name, value):
        """Filtre les sources avec erreurs"""
        if value:
            return queryset.filter(Q(status='error') | Q(error_count__gt=0))
        return queryset.exclude(Q(status='error') | Q(error_count__gt=0))
    
    def filter_min_success_rate(self, queryset, name, value):
        """Filtre par taux de succès minimum"""
        return queryset.filter(success_rate__gte=value)
    
    def filter_health_status(self, queryset, name, value):
        """Filtre par état de santé"""
        if value == 'critical':
            return queryset.filter(consecutive_failures__gte=5)
        elif value == 'warning':
            return queryset.filter(consecutive_failures__gte=3, consecutive_failures__lt=5)
        elif value == 'fair':
            return queryset.filter(data_quality_score__gte=50, data_quality_score__lt=75)
        elif value == 'good':
            return queryset.filter(data_quality_score__gte=75)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Recherche multi-champs"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(host__icontains=value) |
            Q(database_name__icontains=value) |
            Q(owner_team__icontains=value) |
            Q(category__icontains=value)
        )


class DataTableFilter(filters.FilterSet):
    """Filtres pour DataTable"""
    
    data_source = filters.UUIDFilter(field_name='data_source__id', label="ID source")
    data_source_name = filters.CharFilter(field_name='data_source__name', lookup_expr='icontains', label="Nom source")
    name = filters.CharFilter(lookup_expr='icontains', label="Nom table")
    schema = filters.CharFilter(lookup_expr='icontains', label="Schéma")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    
    is_partitioned = filters.BooleanFilter(label="Partitionné")
    has_schema = filters.BooleanFilter(method='filter_has_schema', label="A un schéma")
    
    min_rows = filters.NumberFilter(field_name='row_count', lookup_expr='gte', label="Lignes min")
    max_rows = filters.NumberFilter(field_name='row_count', lookup_expr='lte', label="Lignes max")
    min_columns = filters.NumberFilter(method='filter_min_columns', label="Colonnes min")
    max_columns = filters.NumberFilter(method='filter_max_columns', label="Colonnes max")
    
    last_updated_after = filters.DateTimeFilter(field_name='last_updated', lookup_expr='gte', label="Mis à jour après")
    last_updated_before = filters.DateTimeFilter(field_name='last_updated', lookup_expr='lte', label="Mis à jour avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DataTable
        fields = ['data_source', 'is_partitioned']
    
    def filter_has_schema(self, queryset, name, value):
        if value:
            return queryset.exclude(columns=[])
        return queryset.filter(columns=[])
    
    def filter_min_columns(self, queryset, name, value):
        return queryset.filter(column_count__gte=value)
    
    def filter_max_columns(self, queryset, name, value):
        return queryset.filter(column_count__lte=value)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(schema__icontains=value) |
            Q(description__icontains=value)
        )


class DataQueryFilter(filters.FilterSet):
    """Filtres pour DataQuery"""
    
    data_source = filters.UUIDFilter(field_name='data_source__id')
    data_source_name = filters.CharFilter(field_name='data_source__name', lookup_expr='icontains')
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    query_type = filters.ChoiceFilter(choices=QUERY_TYPES)
    
    is_favorite = filters.BooleanFilter()
    is_public = filters.BooleanFilter()
    is_cached = filters.BooleanFilter()
    
    created_by = filters.UUIDFilter(field_name='created_by__id')
    
    min_executions = filters.NumberFilter(field_name='execution_count', lookup_expr='gte')
    max_executions = filters.NumberFilter(field_name='execution_count', lookup_expr='lte')
    
    last_executed_after = filters.DateTimeFilter(field_name='last_executed', lookup_expr='gte')
    last_executed_before = filters.DateTimeFilter(field_name='last_executed', lookup_expr='lte')
    
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = DataQuery
        fields = ['data_source', 'query_type', 'is_favorite', 'is_public']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(query_text__icontains=value)
        )


# apps/data_sources/filters.py - AJOUTER

class StarSchemaFilter(filters.FilterSet):
    """Filtres pour StarSchema"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    grain = filters.CharFilter(lookup_expr='icontains', label="Grain")
    
    fact_table = filters.UUIDFilter(field_name='fact_table__id', label="ID table des faits")
    fact_table_name = filters.CharFilter(field_name='fact_table__name', lookup_expr='icontains', label="Nom table des faits")
    
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    team = filters.UUIDFilter(field_name='team__id', label="ID équipe")
    
    is_active = filters.BooleanFilter(label="Actif")
    is_public = filters.BooleanFilter(label="Public")
    
    min_measures = filters.NumberFilter(method='filter_min_measures', label="Mesures min")
    min_dimensions = filters.NumberFilter(method='filter_min_dimensions', label="Dimensions min")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = StarSchema
        fields = ['is_active', 'is_public', 'owner', 'team']
    
    def filter_min_measures(self, queryset, name, value):
        result_ids = []
        for schema in queryset:
            if schema.measures_count >= value:
                result_ids.append(schema.id)
        return queryset.filter(id__in=result_ids)
    
    def filter_min_dimensions(self, queryset, name, value):
        return queryset.annotate(
            dim_count=Count('dimension_tables')
        ).filter(dim_count__gte=value)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(grain__icontains=value)
        )

class DataSourceLogFilter(filters.FilterSet):
    """Filtres pour DataSourceLog"""
    
    data_source = filters.UUIDFilter(field_name='data_source__id', label="ID source")
    data_source_name = filters.CharFilter(field_name='data_source__name', lookup_expr='icontains', label="Nom source")
    level = filters.ChoiceFilter(choices=DataSourceLog.LEVEL_CHOICES, label="Niveau")
    
    timestamp_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Après")
    timestamp_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Avant")
    
    min_execution_time = filters.NumberFilter(field_name='execution_time_ms', lookup_expr='gte', label="Temps min (ms)")
    max_execution_time = filters.NumberFilter(field_name='execution_time_ms', lookup_expr='lte', label="Temps max (ms)")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DataSourceLog
        fields = ['data_source', 'level']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(message__icontains=value) |
            Q(query_text__icontains=value)
        )


class DataSourceMetricFilter(filters.FilterSet):
    """Filtres pour DataSourceMetric"""
    
    data_source = filters.UUIDFilter(field_name='data_source__id', label="ID source")
    data_source_name = filters.CharFilter(field_name='data_source__name', lookup_expr='icontains', label="Nom source")
    
    timestamp_after = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte', label="Après")
    timestamp_before = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte', label="Avant")
    
    min_query_time = filters.NumberFilter(field_name='query_time_ms', lookup_expr='gte', label="Temps requête min (ms)")
    max_query_time = filters.NumberFilter(field_name='query_time_ms', lookup_expr='lte', label="Temps requête max (ms)")
    min_rows = filters.NumberFilter(field_name='rows_returned', lookup_expr='gte', label="Lignes min")
    max_rows = filters.NumberFilter(field_name='rows_returned', lookup_expr='lte', label="Lignes max")
    
    class Meta:
        model = DataSourceMetric
        fields = ['data_source']