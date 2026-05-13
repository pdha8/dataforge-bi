# apps/notifications/admin.py
"""
Configuration admin pour l'application notifications
"""
from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin

from .models import Notification, NotificationChannel, Subscription, AlertRule


@admin.register(Notification)
class NotificationAdmin(ImportExportModelAdmin):
    """Administration des notifications"""
    
    list_display = [
        'title_display', 'recipient', 'notification_type_badge',
        'priority_badge', 'status_badge', 'created_at'
    ]
    list_display_links = ['title_display']
    list_filter = ['notification_type', 'priority', 'status', 'created_at']
    search_fields = ['title', 'message', 'recipient__email']
    date_hierarchy = 'created_at'
    list_per_page = 25
    readonly_fields = ['id', 'created_at', 'updated_at', 'sent_at', 'read_at', 'delivered_at']
    
    fieldsets = (
        ('📨 Informations', {
            'fields': ('recipient', 'notification_type', 'title', 'message', 'priority')
        }),
        ('🔗 Liens', {
            'fields': ('dashboard', 'kpi', 'report', 'pipeline'),
            'classes': ('collapse',)
        }),
        ('📊 Métadonnées', {
            'fields': ('metadata', 'channels'),
            'classes': ('collapse',)
        }),
        ('📅 Statut', {
            'fields': ('status', 'sent_at', 'read_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            obj.title, obj.message[:50] + '...' if obj.message else ''
        )
    title_display.short_description = 'Notification'
    
    def notification_type_badge(self, obj):
        icons = {
            'kpi_alert': '📊',
            'kpi_target_reached': '🎯',
            'pipeline_complete': '✅',
            'pipeline_failed': '❌',
            'report_ready': '📄',
            'anomaly_detected': '🔍',
        }
        icon = icons.get(obj.notification_type, '🔔')
        return format_html('{} {}', icon, obj.get_notification_type_display())
    notification_type_badge.short_description = 'Type'
    
    def priority_badge(self, obj):
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'orange',
            'critical': 'danger',
        }
        color = colors.get(obj.priority, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_priority_display())
    priority_badge.short_description = 'Priorité'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'secondary',
            'queued': 'info',
            'sent': 'success',
            'failed': 'danger',
            'delivered': 'success',
            'read': 'primary',
            'archived': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'


@admin.register(NotificationChannel)
class NotificationChannelAdmin(ImportExportModelAdmin):
    """Administration des canaux de notification"""
    
    list_display = ['user', 'channel_badge', 'address', 'is_enabled', 'is_verified', 'last_used']
    list_filter = ['channel', 'is_enabled', 'is_verified']
    search_fields = ['user__email', 'address']
    
    def channel_badge(self, obj):
        icons = {
            'email': '📧',
            'sms': '📱',
            'push': '📲',
            'slack': '💬',
            'teams': '💼',
            'telegram': '✈️',
            'whatsapp': '💚',
            'webhook': '🌐',
        }
        icon = icons.get(obj.channel, '🔔')
        return format_html('{} {}', icon, obj.get_channel_display())
    channel_badge.short_description = 'Canal'


@admin.register(Subscription)
class SubscriptionAdmin(ImportExportModelAdmin):
    """Administration des abonnements"""
    
    list_display = ['user', 'notification_type_badge', 'is_enabled', 'created_at']
    list_filter = ['notification_type', 'is_enabled']
    search_fields = ['user__email']
    
    def notification_type_badge(self, obj):
        return format_html('<span class="badge bg-info">{}</span>', obj.get_notification_type_display())
    notification_type_badge.short_description = 'Type'


@admin.register(AlertRule)
class AlertRuleAdmin(ImportExportModelAdmin):
    """Administration des règles d'alerte"""
    
    list_display = ['name', 'kpi', 'condition_badge', 'threshold', 'trigger_count', 'is_enabled']
    list_filter = ['condition', 'is_enabled', 'check_frequency']
    search_fields = ['name', 'description', 'kpi__name']
    
    def condition_badge(self, obj):
        return format_html('<span class="badge bg-primary">{}</span>', obj.get_condition_display())
    condition_badge.short_description = 'Condition'
