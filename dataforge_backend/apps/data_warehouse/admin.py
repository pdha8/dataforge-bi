# apps/data_warehouse/admin.py
"""
Admin pour l'application data_warehouse
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    DataWarehouseSchema, DataWarehouseTable, FactTable, DimensionTable,
    StarSchema, Measure, DimensionAttribute, AggregationTable,
    DataWarehouseLog, DataWarehouseMetric
)


@admin.register(DataWarehouseSchema)
class DataWarehouseSchemaAdmin(admin.ModelAdmin):
    """Administration des schémas Data Warehouse"""
    
    list_display = ['name', 'table_count', 'size_mb', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['table_count', 'size_bytes', 'last_analyzed', 'created_at', 'updated_at']


@admin.register(DataWarehouseTable)
class DataWarehouseTableAdmin(admin.ModelAdmin):
    """Administration des tables Data Warehouse"""
    
    list_display = ['full_name', 'table_type_badge', 'status_badge', 'row_count', 'size_mb', 'last_refresh']
    list_filter = ['schema', 'table_type', 'status', 'refresh_frequency', 'is_partitioned']
    search_fields = ['name', 'description']
    readonly_fields = ['row_count', 'size_bytes', 'last_refresh', 'refresh_duration_ms', 'created_at', 'updated_at']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Table'
    
    def table_type_badge(self, obj):
        colors = {'fact': 'success', 'dimension': 'info', 'aggregate': 'warning', 'bridge': 'primary', 'staging': 'secondary'}
        color = colors.get(obj.table_type, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_table_type_display())
    table_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {'active': 'success', 'building': 'warning', 'deprecated': 'danger', 'archived': 'secondary'}
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'
    
    def size_mb(self, obj):
        return f"{obj.size_mb:.2f} MB"
    size_mb.short_description = 'Taille'


@admin.register(FactTable)
class FactTableAdmin(admin.ModelAdmin):
    """Administration des tables des faits"""
    
    list_display = ['full_name', 'granularity', 'measures_count', 'row_count', 'size_mb']
    list_filter = ['schema', 'granularity', 'status']
    search_fields = ['name', 'description']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Table'
    
    def measures_count(self, obj):
        return obj.measures.count()
    measures_count.short_description = 'Mesures'
    
    def size_mb(self, obj):
        return f"{obj.size_mb:.2f} MB"
    size_mb.short_description = 'Taille'


@admin.register(DimensionTable)
class DimensionTableAdmin(admin.ModelAdmin):
    """Administration des tables de dimension"""
    
    list_display = ['full_name', 'dimension_type', 'scd_type', 'attributes_count', 'row_count', 'size_mb']
    list_filter = ['schema', 'dimension_type', 'scd_type', 'status']
    search_fields = ['name', 'description']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Table'
    
    def attributes_count(self, obj):
        return obj.attributes.count()
    attributes_count.short_description = 'Attributs'
    
    def size_mb(self, obj):
        return f"{obj.size_mb:.2f} MB"
    size_mb.short_description = 'Taille'


@admin.register(StarSchema)
class StarSchemaAdmin(admin.ModelAdmin):
    """Administration des schémas en étoile"""
    
    list_display = ['name', 'fact_table_link', 'dimension_count', 'measure_count', 'query_count', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['dimension_tables']
    
    def fact_table_link(self, obj):
        url = reverse('admin:data_warehouse_facttable_change', args=[obj.fact_table.id])
        return format_html('<a href="{}">{}</a>', url, obj.fact_table.full_name)
    fact_table_link.short_description = 'Table des faits'
    
    def dimension_count(self, obj):
        return obj.dimension_count
    dimension_count.short_description = 'Dimensions'
    
    def measure_count(self, obj):
        return obj.measure_count
    measure_count.short_description = 'Mesures'


@admin.register(Measure)
class MeasureAdmin(admin.ModelAdmin):
    """Administration des mesures"""
    
    list_display = ['name', 'fact_table_link', 'aggregation_type', 'is_calculated', 'is_active']
    list_filter = ['aggregation_type', 'is_calculated', 'is_active']
    search_fields = ['name', 'description']
    
    def fact_table_link(self, obj):
        url = reverse('admin:data_warehouse_facttable_change', args=[obj.fact_table.id])
        return format_html('<a href="{}">{}</a>', url, obj.fact_table.full_name)
    fact_table_link.short_description = 'Table des faits'


@admin.register(DimensionAttribute)
class DimensionAttributeAdmin(admin.ModelAdmin):
    """Administration des attributs de dimension"""
    
    list_display = ['name', 'dimension_table_link', 'data_type', 'is_key', 'is_hierarchical', 'is_active']
    list_filter = ['data_type', 'is_key', 'is_hierarchical', 'is_active']
    search_fields = ['name', 'description']
    
    def dimension_table_link(self, obj):
        url = reverse('admin:data_warehouse_dimensiontable_change', args=[obj.dimension_table.id])
        return format_html('<a href="{}">{}</a>', url, obj.dimension_table.full_name)
    dimension_table_link.short_description = 'Dimension'


@admin.register(AggregationTable)
class AggregationTableAdmin(admin.ModelAdmin):
    """Administration des tables d'agrégation"""
    
    list_display = ['name', 'base_table_link', 'granularity', 'row_count', 'size_mb', 'compression_ratio']
    list_filter = ['granularity', 'refresh_frequency']
    search_fields = ['name']
    
    def base_table_link(self, obj):
        url = reverse('admin:data_warehouse_datawarehousetable_change', args=[obj.base_table.id])
        return format_html('<a href="{}">{}</a>', url, obj.base_table.full_name)
    base_table_link.short_description = 'Table de base'
    
    def size_mb(self, obj):
        return f"{obj.size_mb:.2f} MB"
    size_mb.short_description = 'Taille'


@admin.register(DataWarehouseLog)
class DataWarehouseLogAdmin(admin.ModelAdmin):
    """Administration des logs (lecture seule)"""
    
    list_display = ['created_at', 'table_link', 'operation_badge', 'level_badge', 'message_short', 'duration_ms']
    list_filter = ['operation', 'level', 'created_at']
    search_fields = ['message']
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'table', 'operation', 'level', 'message',
                       'duration_ms', 'rows_affected', 'query', 'metadata', 'stack_trace')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def table_link(self, obj):
        if obj.table:
            url = reverse('admin:data_warehouse_datawarehousetable_change', args=[obj.table.id])
            return format_html('<a href="{}">{}</a>', url, obj.table.full_name)
        return '-'
    table_link.short_description = 'Table'
    
    def operation_badge(self, obj):
        colors = {'refresh': 'primary', 'query': 'info', 'optimize': 'warning', 'analyze': 'success'}
        color = colors.get(obj.operation, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_operation_display())
    operation_badge.short_description = 'Opération'
    
    def level_badge(self, obj):
        colors = {'info': 'info', 'warning': 'warning', 'error': 'danger', 'debug': 'secondary'}
        color = colors.get(obj.level, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_level_display())
    level_badge.short_description = 'Niveau'
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'


@admin.register(DataWarehouseMetric)
class DataWarehouseMetricAdmin(admin.ModelAdmin):
    """Administration des métriques (lecture seule)"""
    
    list_display = ['timestamp', 'table_link', 'query_time_ms', 'rows_scanned', 'size_mb', 'cache_hit_ratio']
    list_filter = ['timestamp']
    date_hierarchy = 'timestamp'
    readonly_fields = ('id', 'timestamp', 'table', 'query_time_ms', 'rows_scanned',
                       'bytes_read', 'cache_hit_ratio', 'table_size_bytes', 'index_size_bytes',
                       'partition_count', 'compressed_size_bytes', 'compression_ratio', 'custom_metrics')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def table_link(self, obj):
        url = reverse('admin:data_warehouse_datawarehousetable_change', args=[obj.table.id])
        return format_html('<a href="{}">{}</a>', url, obj.table.full_name)
    table_link.short_description = 'Table'
    
    def size_mb(self, obj):
        if obj.table_size_bytes:
            return f"{obj.table_size_bytes / (1024 * 1024):.2f} MB"
        return '-'
    size_mb.short_description = 'Taille table'
