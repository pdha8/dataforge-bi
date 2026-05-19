# apps/star_schema/serializers.py
"""
Sérialiseurs pour l'application star_schema
"""
from rest_framework import serializers
from django.utils import timezone

from .models import (
    DimensionalSchema,
    FactRelationship, 
    DimensionHierarchy,
    CustomCalculation, 
    GalaxySchema
)


class DimensionalSchemaSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DimensionalSchema"""
    
    schema_type_display = serializers.CharField(source='get_schema_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    grain_display = serializers.CharField(source='get_grain_display', read_only=True)
    
    fact_table_count = serializers.IntegerField(read_only=True)
    dimension_table_count = serializers.IntegerField(read_only=True)
    measure_count = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DimensionalSchema
        fields = [
            'id', 'name', 'description', 'schema_type', 'schema_type_display',
            'status', 'status_display', 'version', 'fact_tables', 'dimension_tables',
            'relationships', 'dimension_mapping', 'measures', 'measure_config',
            'calculations', 'default_filters', 'grain', 'grain_display', 'default_join_type',
            'tags', 'category', 'business_domain', 'documentation_url',
            'owner', 'owner_name', 'team', 'team_name', 'created_by', 'created_by_name',
            'query_count', 'last_queried_at', 'avg_query_time_ms',
            'is_cached', 'cache_ttl_seconds', 'fact_table_count', 'dimension_table_count',
            'measure_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'query_count', 'last_queried_at', 'avg_query_time_ms',
            'created_at', 'updated_at'
        ]


class DimensionalSchemaDetailSerializer(DimensionalSchemaSerializer):
    """Sérialiseur détaillé pour DimensionalSchema"""
    
    fact_tables_detail = serializers.SerializerMethodField()
    dimension_tables_detail = serializers.SerializerMethodField()
    measures_detail = serializers.SerializerMethodField()
    generated_sql = serializers.SerializerMethodField()
    
    class Meta(DimensionalSchemaSerializer.Meta):
        fields = DimensionalSchemaSerializer.Meta.fields + [
            'fact_tables_detail', 'dimension_tables_detail', 'measures_detail', 'generated_sql'
        ]
    
    def get_fact_tables_detail(self, obj):
        return [
            {
                'id': ft.id,
                'name': ft.name,
                'schema': ft.schema.name if ft.schema else None,
                'row_count': ft.row_count
            }
            for ft in obj.fact_tables.all()
        ]
    
    def get_dimension_tables_detail(self, obj):
        return [
            {
                'id': dt.id,
                'name': dt.name,
                'schema': dt.schema.name if dt.schema else None,
                'dimension_type': dt.dimension_type
            }
            for dt in obj.dimension_tables.all()
        ]
    
    def get_measures_detail(self, obj):
        return [
            {
                'id': m.id,
                'name': m.name,
                'column': m.column,
                'aggregation_type': m.get_aggregation_type_display(),
                'alias': m.alias
            }
            for m in obj.measures.all()
        ]
    
    def get_generated_sql(self, obj):
        return obj.generate_query()


class DimensionalSchemaCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de DimensionalSchema"""

    class Meta:
        model = DimensionalSchema
        fields = [
            'id', 'name', 'description', 'schema_type', 'fact_tables', 'dimension_tables',
            'relationships', 'dimension_mapping', 'measures', 'measure_config',
            'calculations', 'default_filters', 'grain', 'default_join_type',
            'tags', 'category', 'business_domain', 'documentation_url',
            'owner', 'team', 'is_cached', 'cache_ttl_seconds'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DimensionalSchemaUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mise à jour de DimensionalSchema"""
    
    class Meta:
        model = DimensionalSchema
        fields = [
            'name', 'description', 'status', 'dimension_mapping', 'measures',
            'measure_config', 'calculations', 'default_filters', 'grain',
            'default_join_type', 'tags', 'category', 'business_domain',
            'documentation_url', 'is_cached', 'cache_ttl_seconds'
        ]


class DimensionalSchemaExecuteSerializer(serializers.Serializer):
    """Sérialiseur pour exécution de schéma dimensionnel"""
    
    filters = serializers.JSONField(required=False, help_text="Filtres supplémentaires")
    limit = serializers.IntegerField(required=False, help_text="Limite de résultats")
    offset = serializers.IntegerField(required=False, help_text="Offset pour pagination")
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel'],
        default='json',
        help_text="Format de sortie"
    )


class FactRelationshipSerializer(serializers.ModelSerializer):
    """Sérialiseur pour FactRelationship"""
    
    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)
    join_type_display = serializers.CharField(source='get_join_type_display', read_only=True)
    
    from_fact_name = serializers.CharField(source='from_fact.name', read_only=True)
    to_fact_name = serializers.CharField(source='to_fact.name', read_only=True)
    
    class Meta:
        model = FactRelationship
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DimensionHierarchySerializer(serializers.ModelSerializer):
    """Sérialiseur pour DimensionHierarchy"""
    
    dimension_table_name = serializers.CharField(source='dimension_table.name', read_only=True)
    level_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DimensionHierarchy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomCalculationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour CustomCalculation"""
    
    calculation_type_display = serializers.CharField(source='get_calculation_type_display', read_only=True)
    dimensional_schema_name = serializers.CharField(source='dimensional_schema.name', read_only=True)
    
    class Meta:
        model = CustomCalculation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class GalaxySchemaSerializer(serializers.ModelSerializer):
    """Sérialiseur pour GalaxySchema"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    dimensional_schema_count = serializers.IntegerField(read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = GalaxySchema
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class GalaxySchemaDetailSerializer(GalaxySchemaSerializer):
    """Sérialiseur détaillé pour GalaxySchema"""
    
    dimensional_schemas_detail = serializers.SerializerMethodField()  # ← Changé de star_schemas à dimensional_schemas
    unified_sql = serializers.SerializerMethodField()
    
    class Meta(GalaxySchemaSerializer.Meta):
        # Correction: utiliser dimensional_schemas au lieu de star_schemas
        fields = [
            'id', 'name', 'description', 'dimensional_schemas', 'galaxy_relationships',  # ← Changé
            'schema_graph', 'status', 'owner', 'tags', 'created_at', 'updated_at',
            'status_display', 'dimensional_schema_count', 'owner_name',
            'dimensional_schemas_detail', 'unified_sql'  # ← Changé
        ]
    
    def get_dimensional_schemas_detail(self, obj):  # ← Changé de get_star_schemas_detail
        """Récupère les détails des schémas dimensionnels"""
        return DimensionalSchemaSerializer(obj.dimensional_schemas.all(), many=True).data
    
    def get_unified_sql(self, obj):
        """Génère le SQL unifié"""
        return obj.generate_unified_query()