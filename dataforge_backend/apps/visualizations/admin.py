# apps/visualizations/admin.py
"""
Configuration admin pour l'application visualizations
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin

from .models import (
    Dashboard, Widget, KPI, Report, Favorite, VisualizationActivity
)


@admin.register(Dashboard)
class DashboardAdmin(ImportExportModelAdmin):
    """Administration des tableaux de bord"""
    
    list_display = [
        'name_display', 'dashboard_type_badge', 'status_badge',
        'widget_count', 'view_count', 'favorite_count',
        'owner', 'created_at'
    ]
    list_display_links = ['name_display']
    list_filter = ['dashboard_type', 'status', 'access_level', 'owner', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    fieldsets = (
        ('📊 Informations du tableau de bord', {
            'fields': ('name', 'slug', 'description', 'dashboard_type', 'status')
        }),
        ('🎨 Design et layout', {
            'fields': ('layout', 'theme', 'custom_css', 'custom_js')
        }),
        ('⚙️ Configuration', {
            'fields': ('global_filters', 'refresh_frequency', 'auto_refresh')
        }),
        ('🔒 Accès et permissions', {
            'fields': ('access_level', 'owner', 'team', 'allowed_users')
        }),
        ('📈 Statistiques', {
            'fields': ('view_count', 'favorite_count', 'last_viewed', 'avg_load_time_ms'),
            'classes': ('collapse',)
        }),
        ('📄 Export', {
            'fields': ('allow_export', 'default_export_format'),
            'classes': ('collapse',)
        }),
        ('📝 Métadonnées', {
            'fields': ('tags', 'category', 'thumbnail', 'version', 'version_notes'),
            'classes': ('collapse',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'view_count', 'favorite_count', 'last_viewed']
    filter_horizontal = ['allowed_users']
    
    def name_display(self, obj):
        return format_html(
            '<strong>📊 {}</strong><br><small class="text-muted">{}</small>',
            obj.name, obj.description[:50] + '...' if obj.description else ''
        )
    name_display.short_description = 'Nom'
    
    def dashboard_type_badge(self, obj):
        colors = {
            'analytical': 'primary',
            'operational': 'info',
            'executive': 'success',
            'strategic': 'warning',
            'tactical': 'danger',
            'custom': 'secondary',
        }
        color = colors.get(obj.dashboard_type, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_dashboard_type_display())
    dashboard_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'published': 'success',
            'archived': 'warning',
            'deleted': 'danger',
            'scheduled': 'info',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'
    
    def widget_count(self, obj):
        count = obj.widgets.count()
        return format_html('<span class="badge bg-info">{}</span>', count)
    widget_count.short_description = 'Widgets'
    
    actions = ['publish_dashboards', 'archive_dashboards', 'duplicate_dashboards']
    
    def publish_dashboards(self, request, queryset):
        count = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{count} tableau(x) de bord publié(s).')
    publish_dashboards.short_description = 'Publier la sélection'
    
    def archive_dashboards(self, request, queryset):
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} tableau(x) de bord archivé(s).')
    archive_dashboards.short_description = 'Archiver la sélection'
    
    def duplicate_dashboards(self, request, queryset):
        for dashboard in queryset:
            dashboard.duplicate(request.user)
        self.message_user(request, f'{queryset.count()} tableau(x) de bord dupliqué(s).')
    duplicate_dashboards.short_description = 'Dupliquer la sélection'


@admin.register(Widget)
class WidgetAdmin(ImportExportModelAdmin):
    """Administration des widgets"""
    
    list_display = [
        'name', 'widget_type_badge', 'dashboard', 'dimensional_schema',
        'is_enabled', 'render_count', 'created_at'
    ]
    list_filter = ['widget_type', 'is_enabled', 'cache_enabled', 'dashboard']
    search_fields = ['name', 'description']
    list_per_page = 25
    
    fieldsets = (
        ('📊 Informations du widget', {
            'fields': ('name', 'description', 'widget_type', 'dashboard', 'dimensional_schema')
        }),
        ('⚙️ Configuration', {
            'fields': ('config', 'filters', 'position', 'style')
        }),
        ('🔄 Interactivité', {
            'fields': ('drilldown_enabled', 'drilldown_config'),
            'classes': ('collapse',)
        }),
        ('💾 Cache', {
            'fields': ('cache_enabled', 'cache_ttl_seconds'),
            'classes': ('collapse',)
        }),
        ('📈 Statistiques', {
            'fields': ('render_count', 'avg_render_time_ms', 'last_rendered'),
            'classes': ('collapse',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['render_count', 'avg_render_time_ms', 'last_rendered', 'created_at', 'updated_at']
    
    def widget_type_badge(self, obj):
        icons = {
            'chart': '📊',
            'metric': '📈',
            'table': '📋',
            'text': '📝',
            'image': '🖼️',
            'iframe': '🔗',
            'custom': '⚙️',
        }
        icon = icons.get(obj.widget_type, '📊')
        return format_html('{} {}', icon, obj.get_widget_type_display())
    widget_type_badge.short_description = 'Type'


@admin.register(KPI)
class KPIAdmin(ImportExportModelAdmin):
    """Administration des KPIs"""
    
    list_display = [
        'name', 'kpi_type_badge', 'dimensional_schema', 'measure',
        'current_value', 'trend_display', 'status_badge', 'is_active'
    ]
    list_filter = ['kpi_type', 'is_active', 'track_trend', 'dimensional_schema']
    search_fields = ['name', 'description']
    list_per_page = 25
    
    fieldsets = (
        ('🎯 Informations du KPI', {
            'fields': ('name', 'description', 'kpi_type', 'dimensional_schema', 'measure', 'dashboard')
        }),
        ('⚙️ Configuration', {
            'fields': ('config', 'formula', 'aggregation', 'filters')
        }),
        ('🎯 Cibles et seuils', {
            'fields': ('target_value', 'warning_threshold', 'critical_threshold')
        }),
        ('📊 Formatage', {
            'fields': ('format_string', 'unit', 'decimal_places')
        }),
        ('📈 Tendances', {
            'fields': ('track_trend', 'trend_direction', 'trend_period')
        }),
        ('📉 Valeurs calculées', {
            'fields': ('current_value', 'previous_value', 'trend_percentage', 'last_calculated'),
            'classes': ('collapse',)
        }),
        ('📝 Métadonnées', {
            'fields': ('tags', 'is_active', 'order'),
            'classes': ('collapse',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['current_value', 'previous_value', 'trend_percentage', 'last_calculated', 'created_at', 'updated_at']
    
    def kpi_type_badge(self, obj):
        icons = {
            'number': '🔢',
            'percentage': '📊',
            'currency': '💰',
            'ratio': '📐',
            'trend': '📈',
            'comparison': '⚖️',
        }
        icon = icons.get(obj.kpi_type, '📊')
        return format_html('{} {}', icon, obj.get_kpi_type_display())
    kpi_type_badge.short_description = 'Type'
    
    def trend_display(self, obj):
        if obj.trend_percentage is not None:
            color = 'success' if obj.trend_percentage > 0 else 'danger'
            sign = '+' if obj.trend_percentage > 0 else ''
            return format_html(
                '<span class="badge bg-{}">{}{}%</span>',
                color, sign, obj.trend_percentage
            )
        return mark_safe('<span class="badge bg-secondary">N/A</span>')
    trend_display.short_description = 'Tendance'
    
    def status_badge(self, obj):
        status = obj.get_status()
        colors = {
            'success': 'success',
            'warning': 'warning',
            'critical': 'danger',
            'unknown': 'secondary',
        }
        color = colors.get(status, 'secondary')
        icons = {
            'success': '✅',
            'warning': '⚠️',
            'critical': '🔴',
            'unknown': '❓',
        }
        icon = icons.get(status, '❓')
        return format_html('<span class="badge bg-{}">{} {}</span>', color, icon, status.upper())
    status_badge.short_description = 'Statut'


@admin.register(Report)
class ReportAdmin(ImportExportModelAdmin):
    """Administration des rapports"""
    
    list_display = [
        'name', 'format_badge', 'dashboard', 'schedule',
        'last_generated', 'generation_count', 'is_active'
    ]
    list_filter = ['format', 'is_active', 'dashboard']
    search_fields = ['name', 'description']
    list_per_page = 25
    
    fieldsets = (
        ('📄 Informations du rapport', {
            'fields': ('name', 'description', 'dashboard', 'format')
        }),
        ('⏰ Planification', {
            'fields': ('schedule', 'recipients')
        }),
        ('🎯 Configuration', {
            'fields': ('filters', 'include_metadata', 'include_filters', 'page_size', 'orientation')
        }),
        ('📊 Génération', {
            'fields': ('last_generated', 'last_generated_by', 'generation_count', 'last_error'),
            'classes': ('collapse',)
        }),
        ('📝 Métadonnées', {
            'fields': ('is_active', 'owner', 'tags'),
            'classes': ('collapse',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_generated', 'last_generated_by', 'generation_count', 'last_error', 'created_at', 'updated_at']
    
    def format_badge(self, obj):
        icons = {
            'png': '🖼️',
            'svg': '📐',
            'pdf': '📄',
            'csv': '📊',
            'excel': '📈',
            'json': '🔧',
            'html': '🌐',
            'markdown': '📝',
        }
        icon = icons.get(obj.format, '📄')
        return format_html('{} {}', icon, obj.format.upper())
    format_badge.short_description = 'Format'
    
    actions = ['generate_reports']
    
    def generate_reports(self, request, queryset):
        from .services import ReportGenerationService
        count = 0
        for report in queryset:
            try:
                service = ReportGenerationService(report)
                service.generate(request.user)
                count += 1
            except Exception as e:
                self.message_user(request, f'Erreur pour {report.name}: {e}', level='ERROR')
        self.message_user(request, f'{count} rapport(s) généré(s).')
    generate_reports.short_description = 'Générer la sélection'


@admin.register(Favorite)
class FavoriteAdmin(ImportExportModelAdmin):
    """Administration des favoris"""
    
    list_display = ['user', 'dashboard', 'kpi', 'report', 'order', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['user__email', 'dashboard__name', 'kpi__name', 'report__name']
    list_per_page = 25


@admin.register(VisualizationActivity)
class VisualizationActivityAdmin(ImportExportModelAdmin):
    """Administration des activités de visualisation"""
    
    list_display = ['user', 'activity_type_badge', 'dashboard', 'widget', 'description', 'created_at']
    list_filter = ['activity_type', 'user', 'created_at']
    search_fields = ['user__email', 'description', 'ip_address']
    date_hierarchy = 'created_at'
    list_per_page = 50
    readonly_fields = ['created_at']
    
    def activity_type_badge(self, obj):
        icons = {
            'view': '👁️',
            'export': '📤',
            'share': '🔗',
            'edit': '✏️',
            'favorite': '⭐',
            'comment': '💬',
        }
        icon = icons.get(obj.activity_type, '📊')
        return format_html('{} {}', icon, obj.get_activity_type_display())
    activity_type_badge.short_description = 'Type'
