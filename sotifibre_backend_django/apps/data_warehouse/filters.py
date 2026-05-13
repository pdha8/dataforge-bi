# apps/data_warehouse/filters.py
"""
Filtres pour l'application data_warehouse
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, Count

from .models import (
    DataWarehouseSchema, DataWarehouseTable, FactTable, DimensionTable,
    StarSchema, Measure, DimensionAttribute, AggregationTable
)
from .constants import (
    TABLE_TYPES, DIMENSION_TYPES, SCD_TYPES, GRANULARITIES,
    TABLE_STATUS, REFRESH_FREQUENCIES, AGGREGATION_TYPES,  # ← Added AGGREGATION_TYPES
    COLUMN_TYPES  # ← Added COLUMN_TYPES for DimensionAttribute
)


class DataWarehouseSchemaFilter(filters.FilterSet):
    """Filtres pour DataWarehouseSchema"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    is_active = filters.BooleanFilter(label="Actif")
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DataWarehouseSchema
        fields = ['is_active', 'owner']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


class DataWarehouseTableFilter(filters.FilterSet):
    """Filtres pour DataWarehouseTable"""
    
    # Filtres texte
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    schema = filters.UUIDFilter(field_name='schema__id', label="ID schéma")
    schema_name = filters.CharFilter(field_name='schema__name', lookup_expr='icontains', label="Nom schéma")
    
    # Filtres choix
    table_type = filters.ChoiceFilter(choices=TABLE_TYPES, label="Type de table")
    status = filters.ChoiceFilter(choices=TABLE_STATUS, label="Statut")
    dimension_type = filters.ChoiceFilter(choices=DIMENSION_TYPES, label="Type de dimension")
    scd_type = filters.ChoiceFilter(choices=SCD_TYPES, label="Type SCD")
    granularity = filters.ChoiceFilter(choices=GRANULARITIES, label="Granularité")
    refresh_frequency = filters.ChoiceFilter(choices=REFRESH_FREQUENCIES, label="Fréquence refresh")
    
    # Filtres booléens
    is_partitioned = filters.BooleanFilter(label="Partitionné")
    is_compressed = filters.BooleanFilter(label="Compressé")
    is_active = filters.BooleanFilter(method='filter_is_active', label="Actif")
    
    # Filtres numériques
    min_row_count = filters.NumberFilter(field_name='row_count', lookup_expr='gte', label="Lignes min")
    max_row_count = filters.NumberFilter(field_name='row_count', lookup_expr='lte', label="Lignes max")
    min_size_mb = filters.NumberFilter(method='filter_min_size_mb', label="Taille min (MB)")
    
    # Filtres de dates
    last_refresh_after = filters.DateTimeFilter(field_name='last_refresh', lookup_expr='gte', label="Refresh après")
    last_refresh_before = filters.DateTimeFilter(field_name='last_refresh', lookup_expr='lte', label="Refresh avant")
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    # Filtres relations
    source_table = filters.UUIDFilter(field_name='source_table__id', label="ID table source")
    source_pipeline = filters.UUIDFilter(field_name='source_pipeline__id', label="ID pipeline source")
    technical_owner = filters.UUIDFilter(field_name='technical_owner__id', label="ID propriétaire technique")
    
    # Recherche générale
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DataWarehouseTable
        fields = ['table_type', 'status', 'dimension_type', 'scd_type', 'granularity', 'refresh_frequency']
    
    def filter_is_active(self, queryset, name, value):
        if value:
            return queryset.filter(status='active')
        return queryset.exclude(status='active')
    
    def filter_min_size_mb(self, queryset, name, value):
        min_bytes = value * 1024 * 1024
        return queryset.filter(size_bytes__gte=min_bytes)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


class FactTableFilter(DataWarehouseTableFilter):
    """Filtres pour FactTable"""
    
    has_measures = filters.BooleanFilter(method='filter_has_measures', label="A des mesures")
    
    class Meta(DataWarehouseTableFilter.Meta):
        model = FactTable
    
    def filter_has_measures(self, queryset, name, value):
        if value:
            return queryset.filter(measures__isnull=False).distinct()
        return queryset.filter(measures__isnull=True).distinct()


class DimensionTableFilter(DataWarehouseTableFilter):
    """Filtres pour DimensionTable"""
    
    has_attributes = filters.BooleanFilter(method='filter_has_attributes', label="A des attributs")
    
    class Meta(DataWarehouseTableFilter.Meta):
        model = DimensionTable
    
    def filter_has_attributes(self, queryset, name, value):
        if value:
            return queryset.filter(attributes__isnull=False).distinct()
        return queryset.filter(attributes__isnull=True).distinct()


class StarSchemaFilter(filters.FilterSet):
    """Filtres pour StarSchema"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    
    fact_table = filters.UUIDFilter(field_name='fact_table__id', label="ID table des faits")
    fact_table_name = filters.CharFilter(field_name='fact_table__name', lookup_expr='icontains', label="Nom table des faits")
    
    dimension_table = filters.UUIDFilter(method='filter_dimension_table', label="ID table de dimension")
    
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    is_active = filters.BooleanFilter(label="Actif")
    
    min_queries = filters.NumberFilter(field_name='query_count', lookup_expr='gte', label="Requêtes min")
    min_measures = filters.NumberFilter(method='filter_min_measures', label="Mesures min")
    min_dimensions = filters.NumberFilter(method='filter_min_dimensions', label="Dimensions min")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = StarSchema
        fields = ['is_active', 'owner']
    
    def filter_dimension_table(self, queryset, name, value):
        return queryset.filter(dimension_tables__id=value)
    
    def filter_min_measures(self, queryset, name, value):
        result_ids = []
        for schema in queryset:
            if schema.measure_count >= value:
                result_ids.append(schema.id)
        return queryset.filter(id__in=result_ids)
    
    def filter_min_dimensions(self, queryset, name, value):
        result_ids = []
        for schema in queryset:
            if schema.dimension_count >= value:
                result_ids.append(schema.id)
        return queryset.filter(id__in=result_ids)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


class MeasureFilter(filters.FilterSet):
    """Filtres pour Measure"""
    
    fact_table = filters.UUIDFilter(field_name='fact_table__id', label="ID table des faits")
    fact_table_name = filters.CharFilter(field_name='fact_table__name', lookup_expr='icontains', label="Nom table des faits")
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    alias = filters.CharFilter(lookup_expr='icontains', label="Alias")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    column = filters.CharFilter(lookup_expr='icontains', label="Colonne")
    
    # Use AGGREGATION_TYPES from constants instead of Measure.AGGREGATION_TYPES
    aggregation_type = filters.ChoiceFilter(choices=AGGREGATION_TYPES, label="Type d'agrégation")
    
    is_calculated = filters.BooleanFilter(label="Mesure calculée")
    is_active = filters.BooleanFilter(label="Actif")
    
    min_decimal_places = filters.NumberFilter(field_name='decimal_places', lookup_expr='gte', label="Décimales min")
    max_decimal_places = filters.NumberFilter(field_name='decimal_places', lookup_expr='lte', label="Décimales max")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = Measure
        fields = ['fact_table', 'aggregation_type', 'is_calculated', 'is_active']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(alias__icontains=value) |
            Q(column__icontains=value)
        )


class DimensionAttributeFilter(filters.FilterSet):
    """Filtres pour DimensionAttribute"""
    
    dimension_table = filters.UUIDFilter(field_name='dimension_table__id', label="ID table de dimension")
    dimension_table_name = filters.CharFilter(field_name='dimension_table__name', lookup_expr='icontains', label="Nom table de dimension")
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    column = filters.CharFilter(lookup_expr='icontains', label="Colonne")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    
    # Use COLUMN_TYPES from constants
    data_type = filters.ChoiceFilter(choices=COLUMN_TYPES, label="Type de données")
    
    is_key = filters.BooleanFilter(label="Clé de dimension")
    is_hierarchical = filters.BooleanFilter(label="Hiérarchique")
    is_active = filters.BooleanFilter(label="Actif")
    
    parent_attribute = filters.UUIDFilter(field_name='parent_attribute__id', label="ID attribut parent")
    
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DimensionAttribute
        fields = ['dimension_table', 'data_type', 'is_key', 'is_hierarchical', 'is_active']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(column__icontains=value)
        )


class AggregationTableFilter(filters.FilterSet):
    """Filtres pour AggregationTable"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    base_table = filters.UUIDFilter(field_name='base_table__id', label="ID table de base")
    base_table_name = filters.CharFilter(field_name='base_table__name', lookup_expr='icontains', label="Nom table de base")
    granularity = filters.ChoiceFilter(choices=GRANULARITIES, label="Granularité")
    refresh_frequency = filters.ChoiceFilter(choices=REFRESH_FREQUENCIES, label="Fréquence refresh")
    
    min_row_count = filters.NumberFilter(field_name='row_count', lookup_expr='gte', label="Lignes min")
    max_row_count = filters.NumberFilter(field_name='row_count', lookup_expr='lte', label="Lignes max")
    min_size_mb = filters.NumberFilter(method='filter_min_size_mb', label="Taille min (MB)")
    min_compression = filters.NumberFilter(field_name='compression_ratio', lookup_expr='gte', label="Compression min")
    max_compression = filters.NumberFilter(field_name='compression_ratio', lookup_expr='lte', label="Compression max")
    
    last_refresh_after = filters.DateTimeFilter(field_name='last_refresh', lookup_expr='gte', label="Refresh après")
    last_refresh_before = filters.DateTimeFilter(field_name='last_refresh', lookup_expr='lte', label="Refresh avant")
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = AggregationTable
        fields = ['granularity', 'refresh_frequency']
    
    def filter_min_size_mb(self, queryset, name, value):
        min_bytes = value * 1024 * 1024
        return queryset.filter(size_bytes__gte=min_bytes)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
        )