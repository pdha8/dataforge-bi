# apps/data_sources/admin.py
"""
Admin pour l'application data_sources
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    DataSource, DataTable, DataQuery, StarSchema,
    DataSourceLog, DataSourceMetric, DataSourceHistory
)
from .services import DataSourceService  # ← AJOUT DE CET IMPORT


class DataSourceResource(resources.ModelResource):
    """Resource pour l'import/export des sources de données"""
    
    class Meta:
        model = DataSource
        fields = (
            'id', 'name', 'description', 'source_type', 'database_type',
            'host', 'port', 'database_name', 'status', 'sync_frequency',
            'created_at', 'updated_at'
        )
        export_order = fields


@admin.register(DataSource)
class DataSourceAdmin(ImportExportModelAdmin):
    """Administration des sources de données BI"""
    
    resource_class = DataSourceResource
    
    list_display = [
        'name_display', 'source_type_badge', 'status_badge',
        'connection_info', 'sync_info', 'metrics_info'
    ]
    list_display_links = ['name_display']
    
    list_filter = ['source_type', 'database_type', 'status', 'sync_frequency', 'created_at']
    search_fields = ['name', 'description', 'host', 'database_name']
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    fieldsets = (
        ('📋 Informations générales', {
            'fields': ('name', 'description', 'source_type', 'status')
        }),
        ('🗄️ Configuration base de données', {
            'fields': ('database_type', 'host', 'port', 'database_name', 'username', 'password'),
            'classes': ('collapse',)
        }),
        ('🌐 Configuration API', {
            'fields': ('api_type', 'api_url', 'api_endpoint', 'api_headers', 'api_params'),
            'classes': ('collapse',)
        }),
        ('📁 Configuration fichier', {
            'fields': ('file_type', 'file_path', 'file_url', 'file_encoding', 'file_delimiter'),
            'classes': ('collapse',)
        }),
        ('☁️ Configuration cloud', {
            'fields': ('cloud_provider', 'bucket_name', 'object_key', 'region'),
            'classes': ('collapse',)
        }),
        ('🔐 Authentification', {
            'fields': ('auth_type', 'auth_token', 'api_key', 'api_key_header'),
            'classes': ('collapse',)
        }),
        ('🔄 Synchronisation', {
            'fields': ('sync_frequency', 'auto_refresh_enabled', 'last_sync', 'last_sync_status'),
            'classes': ('collapse',)
        }),
        ('📊 Métriques', {
            'fields': ('total_queries', 'successful_queries', 'failed_queries', 'avg_query_time_ms'),
            'classes': ('collapse',)
        }),
        ('👥 Organisation', {
            'fields': ('owner', 'team', 'tags'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_sync', 'total_queries', 'successful_queries', 'failed_queries', 'avg_query_time_ms']
    
    def name_display(self, obj):
        """Affiche le nom avec l'icône"""
        icon = '🗄️'
        if obj.source_type == 'api':
            icon = '🌐'
        elif obj.source_type == 'file':
            icon = '📁'
        elif obj.source_type == 'cloud':
            icon = '☁️'
        elif obj.source_type == 'streaming':
            icon = '📡'
        elif obj.source_type == 'data_warehouse':
            icon = '🏢'
        
        return format_html(
            '<strong>{} {}</strong><br><small class="text-muted">{}</small>',
            icon, obj.name, obj.description[:50] if obj.description else ''
        )
    name_display.short_description = 'Source de données'
    
    def source_type_badge(self, obj):
        """Badge pour le type de source"""
        colors = {
            'database': 'success',
            'api': 'info',
            'file': 'warning',
            'cloud': 'primary',
            'streaming': 'danger',
            'data_warehouse': 'dark',
            'data_lake': 'secondary',
        }
        color = colors.get(obj.source_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_source_type_display()
        )
    source_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        """Badge pour le statut"""
        colors = {
            'active': 'success',
            'error': 'danger',
            'testing': 'warning',
            'inactive': 'secondary',
            'configuring': 'info',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def connection_info(self, obj):
        """Informations de connexion"""
        if obj.source_type == 'database':
            if obj.host:
                return format_html(
                    '<span title="{}:{}">{}:{}</span>',
                    obj.host, obj.port or 'default',
                    obj.host[:20], obj.port or 'default'
                )
        elif obj.source_type == 'api':
            if obj.api_url:
                return format_html(
                    '<span title="{}">{}</span>',
                    obj.api_url, obj.api_url[:30]
                )
        elif obj.source_type == 'file':
            if obj.file_path:
                return format_html(
                    '<span title="{}">{}</span>',
                    obj.file_path, obj.file_path[:30]
                )
        return '-'
    connection_info.short_description = 'Connexion'
    
    def sync_info(self, obj):
        """Informations de synchronisation"""
        if obj.last_sync:
            delta = timezone.now() - obj.last_sync
            if delta.days > 0:
                sync_ago = f"{delta.days}j"
            elif delta.seconds > 3600:
                sync_ago = f"{delta.seconds // 3600}h"
            elif delta.seconds > 60:
                sync_ago = f"{delta.seconds // 60}m"
            else:
                sync_ago = "maintenant"
            
            return format_html(
                '<span title="{}">{}</span><br><small>{}</small>',
                obj.last_sync, sync_ago, obj.get_sync_frequency_display()
            )
        return format_html('<small>{}</small>', obj.get_sync_frequency_display())
    sync_info.short_description = 'Synchro'
    
    def metrics_info(self, obj):
        """Métriques"""
        success_rate = obj.success_rate
        color = 'success' if success_rate >= 90 else 'warning' if success_rate >= 50 else 'danger'
        return format_html(
            '<div><span class="badge bg-{}">{}</span></div>'
            '<div><small>{}</small></div>',
            color,
            f"{float(success_rate):.0f}%",
            obj.total_queries
        )
    metrics_info.short_description = 'Métriques'
    
    actions = ['test_connection', 'sync_tables', 'export_selected']
    
    def test_connection(self, request, queryset):
        """Teste la connexion des sources sélectionnées"""
        success = 0
        errors = []
        
        for source in queryset:
            service = DataSourceService(source)
            result = service.test_connection()
            if result['success']:
                success += 1
            else:
                errors.append(f"{source.name}: {result.get('error')}")
        
        self.message_user(request, f"✅ {success} source(s) connectée(s) avec succès")
        if errors:
            self.message_user(request, f"❌ Erreurs:\n" + "\n".join(errors[:5]), level='ERROR')
    test_connection.short_description = "🔌 Tester la connexion"
    
    def sync_tables(self, request, queryset):
        """Synchronise les tables des sources sélectionnées"""
        for source in queryset:
            service = DataSourceService(source)
            result = service.sync_tables()
            if result['success']:
                self.message_user(request, f"✅ {source.name}: {result.get('total_tables')} tables synchronisées")
            else:
                self.message_user(request, f"❌ {source.name}: {result.get('error')}", level='ERROR')
    sync_tables.short_description = "🔄 Synchroniser les tables"
    
    def export_selected(self, request, queryset):
        """Export JSON des sources sélectionnées"""
        from django.http import HttpResponse
        import json
        
        data = []
        for source in queryset:
            data.append({
                'id': str(source.id),
                'name': source.name,
                'description': source.description,
                'source_type': source.source_type,
                'database_type': source.database_type,
                'host': source.host,
                'port': source.port,
                'database_name': source.database_name,
                'status': source.status,
                'sync_frequency': source.sync_frequency,
                'created_at': source.created_at.isoformat() if source.created_at else None,
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2, default=str, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="data_sources_export.json"'
        return response
    export_selected.short_description = "📤 Exporter la sélection"


@admin.register(DataTable)
class DataTableAdmin(admin.ModelAdmin):
    """Administration des tables"""
    
    list_display = ['full_name', 'data_source_link', 'row_count', 'column_count', 'last_updated']
    list_filter = ['data_source', 'is_partitioned', 'last_updated']
    search_fields = ['name', 'schema', 'description']
    readonly_fields = ['row_count', 'size_bytes', 'columns', 'primary_key', 'indexes', 'foreign_keys']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Table'
    
    def data_source_link(self, obj):
        url = reverse('admin:data_sources_datasource_change', args=[obj.data_source.id])
        return format_html('<a href="{}">{}</a>', url, obj.data_source.name)
    data_source_link.short_description = 'Source'
    
    def column_count(self, obj):
        return obj.column_count
    column_count.short_description = 'Colonnes'


@admin.register(DataQuery)
class DataQueryAdmin(admin.ModelAdmin):
    """Administration des requêtes"""
    
    list_display = ['name', 'data_source_link', 'query_type', 'is_favorite', 'execution_count', 'last_executed']
    list_filter = ['data_source', 'query_type', 'is_favorite', 'is_public']
    search_fields = ['name', 'description', 'query_text']
    readonly_fields = ['execution_count', 'avg_execution_time_ms', 'last_executed', 'cached_at']
    
    def data_source_link(self, obj):
        url = reverse('admin:data_sources_datasource_change', args=[obj.data_source.id])
        return format_html('<a href="{}">{}</a>', url, obj.data_source.name)
    data_source_link.short_description = 'Source'


@admin.register(StarSchema)
class StarSchemaAdmin(admin.ModelAdmin):
    """Administration des schémas en étoile"""
    
    list_display = ['name', 'fact_table_link', 'dimension_tables_count', 'owner_link']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['dimension_tables']
    
    def fact_table_link(self, obj):
        url = reverse('admin:data_sources_datatable_change', args=[obj.fact_table.id])
        return format_html('<a href="{}">{}</a>', url, obj.fact_table.full_name)
    fact_table_link.short_description = 'Table des faits'
    
    def dimension_tables_count(self, obj):
        return obj.dimension_tables.count()
    dimension_tables_count.short_description = 'Dimensions'
    
    def owner_link(self, obj):
        if obj.owner:
            url = reverse('admin:users_user_change', args=[obj.owner.id])
            return format_html('<a href="{}">{}</a>', url, obj.owner.email)
        return '-'
    owner_link.short_description = 'Propriétaire'


@admin.register(DataSourceLog)
class DataSourceLogAdmin(admin.ModelAdmin):
    """Administration des logs (lecture seule)"""
    
    list_display = ['created_at', 'data_source_link', 'level_badge', 'message_short', 'execution_time_ms']
    list_filter = ['level', 'created_at']
    search_fields = ['message', 'query_text']
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'data_source', 'level', 'message', 'query_id',
                   'query_text', 'execution_time_ms', 'rows_affected', 'data', 'stack_trace')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def data_source_link(self, obj):
        url = reverse('admin:data_sources_datasource_change', args=[obj.data_source.id])
        return format_html('<a href="{}">{}</a>', url, obj.data_source.name)
    data_source_link.short_description = 'Source'
    
    def level_badge(self, obj):
        colors = {'info': 'info', 'warning': 'warning', 'error': 'danger', 'debug': 'secondary'}
        color = colors.get(obj.level, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_level_display())
    level_badge.short_description = 'Niveau'
    
    def message_short(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_short.short_description = 'Message'


@admin.register(DataSourceMetric)
class DataSourceMetricAdmin(admin.ModelAdmin):
    """Administration des métriques (lecture seule)"""
    
    list_display = ['timestamp', 'data_source_link', 'query_time_ms', 'rows_returned']
    list_filter = ['timestamp']
    date_hierarchy = 'timestamp'
    readonly_fields = ('id', 'timestamp', 'data_source', 'query_time_ms', 'rows_returned',
                   'cpu_time_ms', 'io_wait_ms', 'bytes_sent', 'bytes_received',
                   'network_latency_ms', 'connection_time_ms', 'connection_pool_size',
                   'active_connections', 'custom_metrics')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def data_source_link(self, obj):
        url = reverse('admin:data_sources_datasource_change', args=[obj.data_source.id])
        return format_html('<a href="{}">{}</a>', url, obj.data_source.name)
    data_source_link.short_description = 'Source'
