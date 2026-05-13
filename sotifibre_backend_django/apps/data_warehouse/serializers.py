# apps/data_warehouse/serializers.py
"""
Sérialiseurs pour l'application data_warehouse
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import models

from .models import (
    DataWarehouseSchema, DataWarehouseTable, FactTable, DimensionTable,
    StarSchema, Measure, DimensionAttribute, AggregationTable,
    DataWarehouseLog, DataWarehouseMetric
)
from apps.users.serializers import UserMinimalSerializer
from apps.data_sources.serializers import DataTableSerializer


# ============================================================================
# BASE SERIALIZER
# ============================================================================

class BaseDWSerializer(serializers.ModelSerializer):
    """Classe de base pour tous les sérialiseurs Data Warehouse"""
    
    def to_representation(self, instance):
        """Convertit les dates en ISO format et gère les valeurs vides"""
        data = super().to_representation(instance)
        
        datetime_fields = []
        for field in self.Meta.model._meta.get_fields():
            if isinstance(field, models.DateTimeField):
                datetime_fields.append(field.name)
        
        for field in datetime_fields:
            value = data.get(field)
            if value and isinstance(value, str) and value.strip() == '':
                data[field] = None
            elif value and hasattr(instance, field):
                attr = getattr(instance, field)
                if attr:
                    data[field] = attr.isoformat()
        
        return data


# ============================================================================
# SCHÉMAS DATA WAREHOUSE
# ============================================================================

class DataWarehouseSchemaSerializer(BaseDWSerializer):
    """Sérialiseur pour DataWarehouseSchema"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    size_mb = serializers.FloatField(read_only=True)
    table_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DataWarehouseSchema
        fields = [
            'id', 'name', 'description', 'default_tablespace', 'default_compression',
            'owner', 'owner_name', 'tags', 'is_active', 'table_count',
            'size_bytes', 'size_mb', 'last_analyzed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'table_count', 'size_bytes', 'last_analyzed']


class DataWarehouseSchemaCreateSerializer(BaseDWSerializer):
    """Sérialiseur pour création de schéma"""
    
    class Meta:
        model = DataWarehouseSchema
        fields = [
            'name', 'description', 'default_tablespace', 'default_compression',
            'owner', 'tags', 'is_active'
        ]


# ============================================================================
# TABLES DATA WAREHOUSE
# ============================================================================

class ColumnSerializer(serializers.Serializer):
    """Sérialiseur pour les colonnes"""
    name = serializers.CharField(max_length=200)
    data_type = serializers.CharField(max_length=50)
    nullable = serializers.BooleanField(default=True)
    default = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)


class DataWarehouseTableSerializer(BaseDWSerializer):
    """Sérialiseur pour DataWarehouseTable"""
    
    schema_name = serializers.CharField(source='schema.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    table_type_display = serializers.CharField(source='get_table_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    dimension_type_display = serializers.CharField(source='get_dimension_type_display', read_only=True)
    scd_type_display = serializers.CharField(source='get_scd_type_display', read_only=True)
    granularity_display = serializers.CharField(source='get_granularity_display', read_only=True)
    
    size_mb = serializers.FloatField(read_only=True)
    needs_refresh = serializers.BooleanField(read_only=True)
    
    source_table_name = serializers.CharField(source='source_table.full_name', read_only=True)
    source_pipeline_name = serializers.CharField(source='source_pipeline.name', read_only=True)
    technical_owner_name = serializers.CharField(source='technical_owner.get_full_name', read_only=True)
    
    class Meta:
        model = DataWarehouseTable
        fields = [
            'id', 'name', 'full_name', 'schema', 'schema_name', 'table_type', 'table_type_display',
            'description', 'status', 'status_display', 'dimension_type', 'dimension_type_display',
            'scd_type', 'scd_type_display', 'granularity', 'granularity_display',
            'source_table', 'source_table_name', 'source_pipeline', 'source_pipeline_name',
            'columns', 'primary_key', 'foreign_keys', 'indexes',
            'is_partitioned', 'partition_column', 'partition_type', 'partition_expression',
            'partition_count', 'is_compressed', 'tablespace', 'row_count',
            'size_bytes', 'size_mb', 'refresh_frequency', 'last_refresh', 'next_refresh',
            'refresh_duration_ms', 'needs_refresh', 'tags', 'business_owner',
            'technical_owner', 'technical_owner_name', 'documentation_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'row_count', 'size_bytes',
            'last_refresh', 'refresh_duration_ms', 'needs_refresh'
        ]


class FactTableSerializer(DataWarehouseTableSerializer):
    """Sérialiseur pour FactTable"""
    
    measures_count = serializers.IntegerField(read_only=True)
    measures = serializers.SerializerMethodField()
    
    class Meta(DataWarehouseTableSerializer.Meta):
        fields = DataWarehouseTableSerializer.Meta.fields + ['measures_count', 'measures']
    
    def get_measures(self, obj):
        measures = obj.measures.filter(is_active=True)
        return MeasureSerializer(measures, many=True).data


class DimensionTableSerializer(DataWarehouseTableSerializer):
    """Sérialiseur pour DimensionTable"""
    
    attributes_count = serializers.IntegerField(read_only=True)
    attributes = serializers.SerializerMethodField()
    
    class Meta(DataWarehouseTableSerializer.Meta):
        fields = DataWarehouseTableSerializer.Meta.fields + ['attributes_count', 'attributes']
    
    def get_attributes(self, obj):
        attributes = obj.attributes.filter(is_active=True)
        return DimensionAttributeSerializer(attributes, many=True).data


class DataWarehouseTableCreateSerializer(BaseDWSerializer):
    """Sérialiseur pour création de table"""
    
    class Meta:
        model = DataWarehouseTable
        fields = [
            'name', 'schema', 'table_type', 'description', 'source_table', 'source_pipeline',
            'dimension_type', 'scd_type', 'granularity', 'columns', 'primary_key',
            'foreign_keys', 'indexes', 'is_partitioned', 'partition_column',
            'partition_type', 'partition_expression', 'is_compressed', 'tablespace',
            'refresh_frequency', 'tags', 'business_owner', 'technical_owner',
            'documentation_url'
        ]


# ============================================================================
# MESURES ET ATTRIBUTS
# ============================================================================

class MeasureSerializer(BaseDWSerializer):
    """Sérialiseur pour Measure"""
    
    fact_table_name = serializers.CharField(source='fact_table.name', read_only=True)
    aggregation_type_display = serializers.CharField(source='get_aggregation_type_display', read_only=True)
    
    class Meta:
        model = Measure
        fields = [
            'id', 'fact_table', 'fact_table_name', 'name', 'column', 'aggregation_type',
            'aggregation_type_display', 'alias', 'description', 'is_calculated', 'formula',
            'format_string', 'unit', 'decimal_places', 'tags', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MeasureCreateSerializer(BaseDWSerializer):
    """Sérialiseur pour création de mesure"""
    
    class Meta:
        model = Measure
        fields = [
            'fact_table', 'name', 'column', 'aggregation_type', 'alias',
            'description', 'is_calculated', 'formula', 'format_string',
            'unit', 'decimal_places', 'tags', 'is_active'
        ]


class DimensionAttributeSerializer(BaseDWSerializer):
    """Sérialiseur pour DimensionAttribute"""
    
    dimension_table_name = serializers.CharField(source='dimension_table.name', read_only=True)
    data_type_display = serializers.CharField(source='get_data_type_display', read_only=True)
    parent_attribute_name = serializers.CharField(source='parent_attribute.name', read_only=True)
    
    class Meta:
        model = DimensionAttribute
        fields = [
            'id', 'dimension_table', 'dimension_table_name', 'name', 'column', 'data_type',
            'data_type_display', 'description', 'is_key', 'is_hierarchical', 'parent_attribute',
            'parent_attribute_name', 'format_string', 'tags', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DimensionAttributeCreateSerializer(BaseDWSerializer):
    """Sérialiseur pour création d'attribut"""
    
    class Meta:
        model = DimensionAttribute
        fields = [
            'dimension_table', 'name', 'column', 'data_type', 'description',
            'is_key', 'is_hierarchical', 'parent_attribute', 'format_string',
            'tags', 'is_active'
        ]


# ============================================================================
# SCHÉMAS EN ÉTOILE
# ============================================================================

class StarSchemaSerializer(BaseDWSerializer):
    """Sérialiseur pour StarSchema"""
    
    fact_table_name = serializers.CharField(source='fact_table.full_name', read_only=True)
    dimension_tables_detail = serializers.SerializerMethodField()
    dimension_count = serializers.IntegerField(read_only=True)
    measure_count = serializers.IntegerField(read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    generated_sql = serializers.SerializerMethodField()
    
    class Meta:
        model = StarSchema
        fields = [
            'id', 'name', 'description', 'fact_table', 'fact_table_name',
            'dimension_tables', 'dimension_tables_detail', 'dimension_count',
            'fact_columns', 'dimension_columns', 'relationships', 'measure_count',
            'owner', 'owner_name', 'tags', 'is_active', 'query_count',
            'last_queried_at', 'avg_query_time_ms', 'generated_sql',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'query_count', 'last_queried_at',
            'avg_query_time_ms', 'dimension_count', 'measure_count'
        ]
    
    def get_dimension_tables_detail(self, obj):
        return [
            {
                'id': dt.id,
                'name': dt.full_name,
                'type': dt.dimension_type,
                'attributes': [{'name': a.name, 'is_key': a.is_key} for a in dt.attributes.filter(is_active=True)]
            }
            for dt in obj.dimension_tables.all()
        ]
    
    def get_generated_sql(self, obj):
        return obj.generate_query()


class StarSchemaCreateSerializer(BaseDWSerializer):
    """Sérialiseur pour création de schéma en étoile"""
    
    class Meta:
        model = StarSchema
        fields = [
            'name', 'description', 'fact_table', 'dimension_tables',
            'fact_columns', 'dimension_columns', 'relationships',
            'owner', 'tags', 'is_active'
        ]


# ============================================================================
# AGRÉGATIONS
# ============================================================================

class AggregationTableSerializer(BaseDWSerializer):
    """Sérialiseur pour AggregationTable"""
    
    base_table_name = serializers.CharField(source='base_table.full_name', read_only=True)
    granularity_display = serializers.CharField(source='get_granularity_display', read_only=True)
    size_mb = serializers.FloatField(read_only=True)
    
    class Meta:
        model = AggregationTable
        fields = [
            'id', 'name', 'base_table', 'base_table_name', 'granularity', 'granularity_display',
            'group_by_columns', 'aggregated_columns', 'refresh_frequency', 'last_refresh',
            'row_count', 'size_bytes', 'size_mb', 'compression_ratio', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'row_count', 'size_bytes']


# ============================================================================
# LOGS ET MÉTRIQUES
# ============================================================================

class DataWarehouseLogSerializer(BaseDWSerializer):
    """Sérialiseur pour DataWarehouseLog"""
    
    table_name = serializers.CharField(source='table.full_name', read_only=True)
    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    level_icon = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = DataWarehouseLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
    
    def get_level_icon(self, obj):
        icons = {'info': 'ℹ️', 'warning': '⚠️', 'error': '❌', 'debug': '🐛'}
        return icons.get(obj.level, '📝')
    
    def get_time_ago(self, obj):
        from apps.core.utils import format_timesince
        return format_timesince(obj.created_at, default="à l'instant")


class DataWarehouseMetricSerializer(BaseDWSerializer):
    """Sérialiseur pour DataWarehouseMetric"""
    
    table_name = serializers.CharField(source='table.full_name', read_only=True)
    size_mb = serializers.SerializerMethodField()
    index_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = DataWarehouseMetric
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']
    
    def get_size_mb(self, obj):
        if obj.table_size_bytes:
            return round(obj.table_size_bytes / (1024 * 1024), 2)
        return None
    
    def get_index_size_mb(self, obj):
        if obj.index_size_bytes:
            return round(obj.index_size_bytes / (1024 * 1024), 2)
        return None


# ============================================================================
# STATISTIQUES
# ============================================================================

class DataWarehouseStatsSerializer(serializers.Serializer):
    """Statistiques globales Data Warehouse"""
    
    total_schemas = serializers.IntegerField()
    total_tables = serializers.IntegerField()
    fact_tables = serializers.IntegerField()
    dimension_tables = serializers.IntegerField()
    total_size_mb = serializers.FloatField()
    total_rows = serializers.IntegerField()
    star_schemas = serializers.IntegerField()
    aggregations = serializers.IntegerField()


class TableStatsSerializer(serializers.Serializer):
    """Statistiques par table"""
    
    table_name = serializers.CharField()
    table_type = serializers.CharField()
    row_count = serializers.IntegerField()
    size_mb = serializers.FloatField()
    last_refresh = serializers.DateTimeField()
    refresh_duration_ms = serializers.IntegerField()