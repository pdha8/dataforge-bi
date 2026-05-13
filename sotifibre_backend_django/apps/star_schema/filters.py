# apps/star_schema/filters.py
"""
Filtres pour l'application star_schema
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, Count

from .models import (
    DimensionalSchema,  # ← Changé de StarSchema à DimensionalSchema
    FactRelationship, 
    DimensionHierarchy, 
    CustomCalculation,
    GalaxySchema
)
from .constants import (
    SCHEMA_TYPES, STATUS_CHOICES, GRAIN_LEVELS, 
    RELATION_TYPES, CALCULATION_TYPES
)


class DimensionalSchemaFilter(filters.FilterSet):
    """Filtres pour DimensionalSchema"""
    
    # Filtres texte
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    category = filters.CharFilter(lookup_expr='icontains', label="Catégorie")
    business_domain = filters.CharFilter(lookup_expr='icontains', label="Domaine métier")
    
    # Filtres choix
    schema_type = filters.ChoiceFilter(choices=SCHEMA_TYPES, label="Type de schéma")
    status = filters.ChoiceFilter(choices=STATUS_CHOICES, label="Statut")
    grain = filters.ChoiceFilter(choices=GRAIN_LEVELS, label="Grain")
    
    # Filtres booléens
    is_cached = filters.BooleanFilter(label="En cache")
    has_measures = filters.BooleanFilter(method='filter_has_measures', label="A des mesures")
    has_dimensions = filters.BooleanFilter(method='filter_has_dimensions', label="A des dimensions")
    
    # Filtres numériques
    min_queries = filters.NumberFilter(field_name='query_count', lookup_expr='gte', label="Requêtes min")
    max_queries = filters.NumberFilter(field_name='query_count', lookup_expr='lte', label="Requêtes max")
    min_avg_time = filters.NumberFilter(field_name='avg_query_time_ms', lookup_expr='gte', label="Temps moyen min (ms)")
    max_avg_time = filters.NumberFilter(field_name='avg_query_time_ms', lookup_expr='lte', label="Temps moyen max (ms)")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label="Créé avant")
    last_queried_after = filters.DateTimeFilter(field_name='last_queried_at', lookup_expr='gte', label="Interrogé après")
    
    # Filtres relations
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    team = filters.UUIDFilter(field_name='team__id', label="ID équipe")
    fact_table = filters.UUIDFilter(method='filter_fact_table', label="ID table de faits")
    dimension_table = filters.UUIDFilter(method='filter_dimension_table', label="ID table de dimension")
    
    # Recherche générale
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = DimensionalSchema
        fields = ['schema_type', 'status', 'grain', 'owner', 'team']
    
    def filter_has_measures(self, queryset, name, value):
        if value:
            return queryset.filter(measures__isnull=False).distinct()
        return queryset.filter(measures__isnull=True).distinct()
    
    def filter_has_dimensions(self, queryset, name, value):
        if value:
            return queryset.exclude(dimension_mapping={})
        return queryset.filter(dimension_mapping={})
    
    def filter_fact_table(self, queryset, name, value):
        return queryset.filter(fact_tables__id=value)
    
    def filter_dimension_table(self, queryset, name, value):
        return queryset.filter(dimension_tables__id=value)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(category__icontains=value) |
            Q(business_domain__icontains=value)
        )


class FactRelationshipFilter(filters.FilterSet):
    """Filtres pour FactRelationship"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    from_fact = filters.UUIDFilter(field_name='from_fact__id', label="ID table source")
    to_fact = filters.UUIDFilter(field_name='to_fact__id', label="ID table cible")
    relation_type = filters.ChoiceFilter(choices=RELATION_TYPES, label="Type de relation")
    is_enabled = filters.BooleanFilter(label="Activée")
    
    class Meta:
        model = FactRelationship
        fields = ['relation_type', 'is_enabled']


class DimensionHierarchyFilter(filters.FilterSet):
    """Filtres pour DimensionHierarchy"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    dimension_table = filters.UUIDFilter(field_name='dimension_table__id', label="ID table de dimension")
    is_active = filters.BooleanFilter(label="Active")
    
    class Meta:
        model = DimensionHierarchy
        fields = ['dimension_table', 'is_active']


class CustomCalculationFilter(filters.FilterSet):
    """Filtres pour CustomCalculation"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    dimensional_schema = filters.UUIDFilter(field_name='dimensional_schema__id', label="ID schéma dimensionnel")
    calculation_type = filters.ChoiceFilter(choices=CALCULATION_TYPES, label="Type de calcul")
    is_active = filters.BooleanFilter(label="Actif")
    
    class Meta:
        model = CustomCalculation
        fields = ['dimensional_schema', 'calculation_type', 'is_active']


class GalaxySchemaFilter(filters.FilterSet):
    """Filtres pour GalaxySchema"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    status = filters.ChoiceFilter(choices=STATUS_CHOICES, label="Statut")
    owner = filters.UUIDFilter(field_name='owner__id', label="ID propriétaire")
    dimensional_schema = filters.UUIDFilter(method='filter_dimensional_schema', label="ID schéma dimensionnel")
    
    search = filters.CharFilter(method='filter_search', label="Recherche")
    
    class Meta:
        model = GalaxySchema
        fields = ['status', 'owner']
    
    def filter_dimensional_schema(self, queryset, name, value):
        return queryset.filter(dimensional_schemas__id=value)
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )