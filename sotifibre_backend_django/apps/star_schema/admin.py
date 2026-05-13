# apps/star_schema/admin.py
"""
Configuration admin pour l'application star_schema
"""
from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from .models import (
    DimensionalSchema,  # ← Renommé
    FactRelationship, 
    DimensionHierarchy, 
    GalaxySchema,
    CustomCalculation
)


@admin.register(DimensionalSchema)  # ← Renommé
class DimensionalSchemaAdmin(ImportExportModelAdmin):
    """Administration des schémas dimensionnels"""
    
    list_display = [
        'name_display', 'schema_type_badge', 'status_badge',
        'fact_tables_count', 'dimension_tables_count', 'measure_count',
        'query_count', 'is_active_badge'
    ]
    list_display_links = ['name_display']
    list_filter = ['schema_type', 'status', 'grain', 'is_cached', 'created_at']
    search_fields = ['name', 'description', 'category', 'business_domain']
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    fieldsets = (
        ('⭐ Informations du schéma', {
            'fields': ('name', 'description', 'schema_type', 'status', 'version')
        }),
        ('📊 Tables et relations', {
            'fields': ('fact_tables', 'dimension_tables', 'relationships')
        }),
        ('📐 Modélisation', {
            'fields': ('dimension_mapping', 'measures', 'measure_config', 'calculations', 'grain', 'default_join_type')
        }),
        ('🎯 Filtres', {
            'fields': ('default_filters',),
            'classes': ('collapse',)
        }),
        ('🏷️ Métadonnées', {
            'fields': ('tags', 'category', 'business_domain', 'documentation_url')
        }),
        ('👥 Propriétaires', {
            'fields': ('owner', 'team', 'created_by')
        }),
        ('⚡ Performance', {
            'fields': ('query_count', 'last_queried_at', 'avg_query_time_ms', 'is_cached', 'cache_ttl_seconds'),
            'classes': ('collapse',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'query_count', 'last_queried_at', 'avg_query_time_ms']
    
    filter_horizontal = ['fact_tables', 'dimension_tables', 'measures']
    
    def name_display(self, obj):
        return format_html(
            '<strong>⭐ {}</strong><br><small class="text-muted">{}</small>',
            obj.name, obj.description[:50] + '...' if obj.description else ''
        )
    name_display.short_description = 'Nom'
    
    def schema_type_badge(self, obj):
        colors = {
            'star': 'primary',
            'snowflake': 'info',
            'galaxy': 'warning',
            'constellation': 'success',
        }
        color = colors.get(obj.schema_type, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_schema_type_display())
    schema_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'active': 'success',
            'archived': 'warning',
            'deprecated': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'
    
    def fact_tables_count(self, obj):
        return obj.fact_tables.count()
    fact_tables_count.short_description = 'Faits'
    
    def dimension_tables_count(self, obj):
        return obj.dimension_tables.count()
    dimension_tables_count.short_description = 'Dimensions'
    
    def measure_count(self, obj):
        return obj.measures.count()
    measure_count.short_description = 'Mesures'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge bg-success">✅ Actif</span>')
        return format_html('<span class="badge bg-secondary">⏸️ Inactif</span>')
    is_active_badge.short_description = 'Actif'


@admin.register(FactRelationship)
class FactRelationshipAdmin(ImportExportModelAdmin):
    """Administration des relations entre faits"""
    
    list_display = ['name', 'from_fact', 'to_fact', 'relation_type_badge', 'is_enabled_badge', 'cardinality']
    list_filter = ['relation_type', 'join_type', 'is_enabled']
    search_fields = ['name']
    
    def relation_type_badge(self, obj):
        return format_html('<span class="badge bg-info">{}</span>', obj.get_relation_type_display())
    relation_type_badge.short_description = 'Type'
    
    def is_enabled_badge(self, obj):
        if obj.is_enabled:
            return format_html('<span class="badge bg-success">✅ Activée</span>')
        return format_html('<span class="badge bg-secondary">⏸️ Désactivée</span>')
    is_enabled_badge.short_description = 'Activée'


@admin.register(DimensionHierarchy)
class DimensionHierarchyAdmin(ImportExportModelAdmin):
    """Administration des hiérarchies de dimensions"""
    
    list_display = ['name', 'dimension_table', 'level_count', 'is_active_badge']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def level_count(self, obj):
        return len(obj.levels) if obj.levels else 0
    level_count.short_description = 'Niveaux'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge bg-success">✅ Active</span>')
        return format_html('<span class="badge bg-secondary">⏸️ Inactive</span>')
    is_active_badge.short_description = 'Active'


@admin.register(CustomCalculation)
class CustomCalculationAdmin(ImportExportModelAdmin):
    """Administration des calculs personnalisés"""
    
    list_display = ['name', 'dimensional_schema', 'calculation_type_badge', 'result_column', 'is_active_badge']
    list_filter = ['calculation_type', 'is_active']
    search_fields = ['name', 'description']
    
    def calculation_type_badge(self, obj):
        return format_html('<span class="badge bg-primary">{}</span>', obj.get_calculation_type_display())
    calculation_type_badge.short_description = 'Type'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge bg-success">✅ Actif</span>')
        return format_html('<span class="badge bg-secondary">⏸️ Inactif</span>')
    is_active_badge.short_description = 'Actif'


@admin.register(GalaxySchema)
class GalaxySchemaAdmin(ImportExportModelAdmin):
    """Administration des schémas galaxie"""
    
    list_display = ['name', 'dimensional_schema_count', 'status_badge', 'owner']
    list_filter = ['status']
    search_fields = ['name', 'description']
    filter_horizontal = ['dimensional_schemas']
    
    def dimensional_schema_count(self, obj):
        return obj.dimensional_schemas.count()
    dimensional_schema_count.short_description = 'Schémas dimensionnels'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'active': 'success',
            'archived': 'warning',
            'deprecated': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'
