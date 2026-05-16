# apps/etl_engine/admin.py
"""
Admin pour l'application etl_engine
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    ETLPipeline, Transformation, ExecutionLog,
    TargetSchema, SourceSchema, PipelineNotification
)


class ETLPipelineResource(resources.ModelResource):
    """Resource pour l'import/export des pipelines"""
    
    class Meta:
        model = ETLPipeline
        fields = (
            'id', 'name', 'description', 'pipeline_type', 'status',
            'schedule_enabled', 'schedule_frequency', 'created_at'
        )
        export_order = fields


@admin.register(ETLPipeline)
class ETLPipelineAdmin(ImportExportModelAdmin):
    """Administration des pipelines ETL"""
    
    resource_class = ETLPipelineResource
    
    list_display = [
        'name_display', 'pipeline_type_badge', 'status_badge',
        'schedule_info', 'execution_info', 'health_badge'
    ]
    list_display_links = ['name_display']
    
    list_filter = ['pipeline_type', 'status', 'schedule_enabled', 'created_at']
    search_fields = ['name', 'description', 'category']
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    fieldsets = (
        ('📋 Informations générales', {
            'fields': ('name', 'description', 'pipeline_type', 'status', 'version')
        }),
        ('🗄️ Source', {
            'fields': ('source', 'source_endpoint_type', 'source_config'),
            'classes': ('collapse',)
        }),
        ('🎯 Cible', {
            'fields': ('target', 'target_endpoint_type', 'target_config'),
            'classes': ('collapse',)
        }),
        ('🔄 Transformations', {
            'fields': ('transformations', 'transformation_order'),
            'classes': ('collapse',)
        }),
        ('⏰ Planification', {
            'fields': ('schedule_enabled', 'schedule_frequency', 'schedule_cron'),
            'classes': ('collapse',)
        }),
        ('⚙️ Paramètres', {
            'fields': ('batch_size', 'timeout_seconds', 'max_errors', 'error_strategy', 'processing_mode'),
            'classes': ('collapse',)
        }),
        ('🔗 Dépendances', {
            'fields': ('dependencies', 'dependency_graph'),
            'classes': ('collapse',)
        }),
        ('🔔 Notifications', {
            'fields': ('notifications_enabled', 'notification_channels', 
                      'notify_on_success', 'notify_on_failure', 'notify_on_start'),
            'classes': ('collapse',)
        }),
        ('📊 Métriques', {
            'fields': ('execution_count', 'success_count', 'failure_count', 
                      'avg_duration_seconds', 'total_rows_processed', 'data_quality_score'),
            'classes': ('collapse',)
        }),
        ('🏷️ Organisation', {
            'fields': ('tags', 'category', 'priority', 'owner', 'team', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'created_at', 'updated_at', 'last_execution', 'next_execution',
        'execution_count', 'success_count', 'failure_count',
        'avg_duration_seconds', 'total_rows_processed', 'data_quality_score'
    )
    
    def name_display(self, obj):
        icon = '🔄'
        if obj.pipeline_type == 'extract':
            icon = '📤'
        elif obj.pipeline_type == 'load':
            icon = '📥'
        elif obj.pipeline_type == 'replication':
            icon = '📋'
        elif obj.pipeline_type == 'cleaning':
            icon = '🧹'
        
        return format_html(
            '<strong>{} {}</strong><br><small class="text-muted">{}</small>',
            icon, obj.name, obj.description[:50] if obj.description else ''
        )
    name_display.short_description = 'Pipeline'
    
    def pipeline_type_badge(self, obj):
        colors = {
            'extract': 'info',
            'load': 'success',
            'etl': 'primary',
            'elt': 'purple',
            'replication': 'warning',
            'migration': 'danger',
            'aggregation': 'secondary',
            'cleaning': 'dark',
        }
        color = colors.get(obj.pipeline_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_pipeline_type_display()
        )
    pipeline_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'active': 'success',
            'draft': 'secondary',
            'paused': 'warning',
            'error': 'danger',
            'archived': 'dark',
            'deprecated': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def schedule_info(self, obj):
        if obj.schedule_enabled:
            if obj.schedule_cron:
                schedule = f"CRON: {obj.schedule_cron}"
            else:
                schedule = obj.get_schedule_frequency_display()
            
            if obj.next_execution:
                delta = obj.next_execution - timezone.now()
                if delta.days > 0:
                    eta = f"dans {delta.days}j"
                elif delta.seconds > 3600:
                    eta = f"dans {delta.seconds // 3600}h"
                elif delta.seconds > 60:
                    eta = f"dans {delta.seconds // 60}m"
                else:
                    eta = "bientôt"
                return format_html(
                    '<span title="{}">⏰ {}</span><br><small>{}</small>',
                    obj.next_execution, schedule, eta
                )
            return schedule
        return 'Manuel'
    schedule_info.short_description = 'Planification'
    
    def execution_info(self, obj):
        success_rate = obj.success_rate
        color = 'success' if success_rate >= 90 else 'warning' if success_rate >= 50 else 'danger'
        return format_html(
            '<div><span class="badge bg-{}">{}</span></div>'
            '<div><small>{}</small></div>',
            color, f"{success_rate:.0f}%", obj.execution_count
        )
    execution_info.short_description = 'Exécutions'
    
    def health_badge(self, obj):
        badges = {
            'critical': ('danger', '🔴'),
            'warning': ('warning', '🟠'),
            'poor': ('warning', '🟡'),
            'fair': ('info', '🟡'),
            'good': ('success', '🟢'),
        }
        color, icon = badges.get(obj.health_status, ('secondary', '⚪'))
        return format_html(
            '<span class="badge bg-{}" title="{}">{}</span>',
            color, obj.health_status.upper(), icon
        )
    health_badge.short_description = 'Santé'
    
    actions = ['execute_pipeline', 'activate_pipelines', 'pause_pipelines']
    
    def execute_pipeline(self, request, queryset):
        from .services import ETLOrchestrator
        orchestrator = ETLOrchestrator()
        success = 0
        for pipeline in queryset:
            result = orchestrator.execute_pipeline(pipeline.id, triggered_by='admin', user=request.user)
            if result['success']:
                success += 1
        self.message_user(request, f'✅ {success} pipeline(s) exécuté(s)')
    execute_pipeline.short_description = "▶️ Exécuter la sélection"
    
    def activate_pipelines(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'✅ {updated} pipeline(s) activé(s)')
    activate_pipelines.short_description = "✅ Activer la sélection"
    
    def pause_pipelines(self, request, queryset):
        updated = queryset.update(status='paused')
        self.message_user(request, f'⏸️ {updated} pipeline(s) mis en pause')
    pause_pipelines.short_description = "⏸️ Mettre en pause"


@admin.register(Transformation)
class TransformationAdmin(admin.ModelAdmin):
    """Administration des transformations"""
    
    list_display = ['name', 'pipeline_link', 'transformation_type', 'order', 'is_enabled', 'execution_count']
    list_filter = ['transformation_type', 'is_enabled', 'is_critical']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_enabled']
    
    def pipeline_link(self, obj):
        url = reverse('admin:etl_engine_etlpipeline_change', args=[obj.pipeline.id])
        return format_html('<a href="{}">{}</a>', url, obj.pipeline.name)
    pipeline_link.short_description = 'Pipeline'


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    """Administration des exécutions (lecture seule)"""
    
    list_display = ['execution_id', 'pipeline_link', 'status_badge', 'started_at', 'duration_short', 'rows_processed']
    list_filter = ['status', 'triggered_by', 'started_at']
    search_fields = ['execution_id', 'error_message']
    date_hierarchy = 'started_at'
    readonly_fields = (  # ← CORRIGÉ: utiliser un tuple au lieu de '__all__'
        'id', 'pipeline', 'execution_id', 'status', 'started_at', 'completed_at',
        'duration_seconds', 'rows_read', 'rows_written', 'rows_errors', 'triggered_by',
        'triggered_by_user', 'result_summary', 'error_message', 'error_traceback',
        'execution_metadata', 'transformation_logs', 'created_at', 'updated_at'
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def pipeline_link(self, obj):
        url = reverse('admin:etl_engine_etlpipeline_change', args=[obj.pipeline.id])
        return format_html('<a href="{}">{}</a>', url, obj.pipeline.name)
    pipeline_link.short_description = 'Pipeline'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'secondary',
            'running': 'primary',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'warning',
            'skipped': 'info',
            'retrying': 'warning',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'
    
    def duration_short(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            elif obj.duration_seconds < 3600:
                return f"{obj.duration_seconds / 60:.1f}m"
            else:
                return f"{obj.duration_seconds / 3600:.1f}h"
        return '-'
    duration_short.short_description = 'Durée'
    
    def rows_processed(self, obj):
        return f"{obj.rows_read:,} → {obj.rows_written:,}"
    rows_processed.short_description = 'Lignes'


@admin.register(TargetSchema)
class TargetSchemaAdmin(admin.ModelAdmin):
    """Administration des schémas cibles"""
    
    list_display = ['pipeline_link', 'table_name', 'insert_strategy', 'is_partitioned']
    list_filter = ['insert_strategy', 'is_partitioned']
    search_fields = ['table_name', 'schema_name']
    
    def pipeline_link(self, obj):
        url = reverse('admin:etl_engine_etlpipeline_change', args=[obj.pipeline.id])
        return format_html('<a href="{}">{}</a>', url, obj.pipeline.name)
    pipeline_link.short_description = 'Pipeline'


@admin.register(SourceSchema)
class SourceSchemaAdmin(admin.ModelAdmin):
    """Administration des schémas sources"""
    
    list_display = ['pipeline_link', 'table_name', 'incremental_column', 'last_value']
    list_filter = ['created_at']
    search_fields = ['table_name', 'query']
    
    def pipeline_link(self, obj):
        url = reverse('admin:etl_engine_etlpipeline_change', args=[obj.pipeline.id])
        return format_html('<a href="{}">{}</a>', url, obj.pipeline.name)
    pipeline_link.short_description = 'Pipeline'


@admin.register(PipelineNotification)
class PipelineNotificationAdmin(admin.ModelAdmin):
    """Administration des notifications"""
    
    list_display = ['pipeline_link', 'channel', 'recipient', 'send_on_failure', 'send_on_success', 'is_enabled']
    list_filter = ['channel', 'is_enabled', 'send_on_failure', 'send_on_success']
    search_fields = ['recipient']
    
    def pipeline_link(self, obj):
        url = reverse('admin:etl_engine_etlpipeline_change', args=[obj.pipeline.id])
        return format_html('<a href="{}">{}</a>', url, obj.pipeline.name)
    pipeline_link.short_description = 'Pipeline'
