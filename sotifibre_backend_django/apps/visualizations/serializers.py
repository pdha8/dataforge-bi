# apps/visualizations/serializers.py
"""
Sérialiseurs pour l'application visualizations
"""
from rest_framework import serializers
from django.utils import timezone

from .models import (
    Dashboard, Widget, KPI, Report, Favorite, VisualizationActivity
)


class DashboardSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Dashboard"""
    
    dashboard_type_display = serializers.CharField(source='get_dashboard_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    access_level_display = serializers.CharField(source='get_access_level_display', read_only=True)
    
    widget_count = serializers.IntegerField(read_only=True)
    chart_count = serializers.IntegerField(read_only=True)
    kpi_count = serializers.IntegerField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    published_by_name = serializers.CharField(source='published_by.get_full_name', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'slug', 'description', 'dashboard_type', 'dashboard_type_display',
            'status', 'status_display', 'layout', 'theme', 'custom_css', 'custom_js',
            'is_fullscreen', 'show_toolbar', 'show_filters', 'global_filters',
            'refresh_frequency', 'auto_refresh', 'last_refresh', 'next_refresh',
            'tags', 'category', 'thumbnail', 'access_level', 'access_level_display',
            'owner', 'owner_name', 'team', 'team_name', 'allowed_users',
            'view_count', 'favorite_count', 'last_viewed', 'avg_load_time_ms',
            'allow_export', 'default_export_format', 'version', 'version_notes',
            'published_at', 'published_by', 'published_by_name',
            'widget_count', 'chart_count', 'kpi_count', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'view_count', 'favorite_count', 'last_viewed',
            'avg_load_time_ms', 'version', 'created_at', 'updated_at'
        ]


class DashboardDetailSerializer(DashboardSerializer):
    """Sérialiseur détaillé pour Dashboard"""
    
    widgets = serializers.SerializerMethodField()
    kpis = serializers.SerializerMethodField()
    
    class Meta(DashboardSerializer.Meta):
        fields = DashboardSerializer.Meta.fields + ['widgets', 'kpis']
    
    def get_widgets(self, obj):
        from .serializers import WidgetSerializer
        return WidgetSerializer(obj.widgets.filter(is_enabled=True), many=True).data
    
    def get_kpis(self, obj):
        from .serializers import KPISerializer
        return KPISerializer(obj.kpis.filter(is_active=True), many=True).data


class DashboardCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de Dashboard"""
    
    class Meta:
        model = Dashboard
        fields = [
            'name', 'description', 'dashboard_type', 'layout', 'theme',
            'global_filters', 'refresh_frequency', 'auto_refresh',
            'tags', 'category', 'access_level', 'owner', 'team',
            'allow_export', 'default_export_format'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DashboardUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mise à jour de Dashboard"""
    
    class Meta:
        model = Dashboard
        fields = [
            'name', 'description', 'status', 'layout', 'theme',
            'custom_css', 'custom_js', 'is_fullscreen', 'show_toolbar',
            'show_filters', 'global_filters', 'refresh_frequency',
            'auto_refresh', 'tags', 'category', 'thumbnail',
            'access_level', 'owner', 'team', 'allowed_users',
            'allow_export', 'default_export_format', 'version_notes'
        ]


class WidgetSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Widget"""
    
    widget_type_display = serializers.CharField(source='get_widget_type_display', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    dimensional_schema_name = serializers.CharField(source='dimensional_schema.name', read_only=True)
    
    class Meta:
        model = Widget
        fields = [
            'id', 'name', 'description', 'widget_type', 'widget_type_display',
            'dashboard', 'dashboard_name', 'dimensional_schema', 'dimensional_schema_name',
            'config', 'position', 'filters', 'style', 'drilldown_enabled',
            'drilldown_config', 'cache_enabled', 'cache_ttl_seconds',
            'is_enabled', 'refresh_on_load', 'order', 'render_count',
            'avg_render_time_ms', 'last_rendered', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'render_count', 'avg_render_time_ms', 'last_rendered',
            'created_at', 'updated_at'
        ]


class KPISerializer(serializers.ModelSerializer):
    """Sérialiseur pour KPI"""
    
    kpi_type_display = serializers.CharField(source='get_kpi_type_display', read_only=True)
    trend_direction_display = serializers.CharField(source='get_trend_direction_display', read_only=True)
    dimensional_schema_name = serializers.CharField(source='dimensional_schema.name', read_only=True)
    measure_name = serializers.CharField(source='measure.name', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    
    status = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    status_icon = serializers.SerializerMethodField()
    
    class Meta:
        model = KPI
        fields = [
            'id', 'name', 'description', 'kpi_type', 'kpi_type_display',
            'dimensional_schema', 'dimensional_schema_name', 'measure', 'measure_name',
            'dashboard', 'dashboard_name', 'config', 'formula', 'aggregation',
            'filters', 'target_value', 'warning_threshold', 'critical_threshold',
            'format_string', 'unit', 'decimal_places', 'track_trend',
            'trend_direction', 'trend_direction_display', 'trend_period',
            'tags', 'is_active', 'order', 'current_value', 'previous_value',
            'trend_percentage', 'last_calculated', 'status', 'status_color',
            'status_icon', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_value', 'previous_value', 'trend_percentage',
            'last_calculated', 'created_at', 'updated_at'
        ]
    
    def get_status(self, obj):
        return obj.get_status()
    
    def get_status_color(self, obj):
        return obj.get_status_color()
    
    def get_status_icon(self, obj):
        return obj.get_status_icon()


class ReportSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Report"""
    
    format_display = serializers.CharField(source='get_format_display', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    next_run = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'dashboard', 'dashboard_name',
            'format', 'format_display', 'schedule', 'recipients', 'filters',
            'include_metadata', 'include_filters', 'page_size', 'orientation',
            'last_generated', 'last_generated_by', 'generation_count',
            'last_error', 'is_active', 'owner', 'owner_name', 'tags',
            'next_run', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_generated', 'last_generated_by', 'generation_count',
            'last_error', 'created_at', 'updated_at'
        ]
    
    def get_next_run(self, obj):
        next_run = obj.get_next_run()
        return next_run.isoformat() if next_run else None


class FavoriteSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Favorite"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    kpi_name = serializers.CharField(source='kpi.name', read_only=True)
    report_name = serializers.CharField(source='report.name', read_only=True)
    
    class Meta:
        model = Favorite
        fields = [
            'id', 'user', 'user_name', 'dashboard', 'dashboard_name',
            'kpi', 'kpi_name', 'report', 'report_name', 'order', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VisualizationActivitySerializer(serializers.ModelSerializer):
    """Sérialiseur pour VisualizationActivity"""
    
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    widget_name = serializers.CharField(source='widget.name', read_only=True)
    
    class Meta:
        model = VisualizationActivity
        fields = [
            'id', 'user', 'user_name', 'dashboard', 'dashboard_name',
            'widget', 'widget_name', 'activity_type', 'activity_type_display',
            'description', 'metadata', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']