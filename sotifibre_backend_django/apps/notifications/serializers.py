# apps/notifications/serializers.py
"""
Sérialiseurs pour l'application notifications
"""
from rest_framework import serializers
from django.utils import timezone

from .models import Notification, NotificationChannel, Subscription, AlertRule


class NotificationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Notification"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    
    dashboard_name = serializers.CharField(source='dashboard.name', read_only=True)
    kpi_name = serializers.CharField(source='kpi.name', read_only=True)
    report_name = serializers.CharField(source='report.name', read_only=True)
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    
    icon = serializers.CharField(read_only=True)
    color = serializers.CharField(read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_name', 'recipient_email',
            'notification_type', 'notification_type_display',
            'title', 'message', 'priority', 'priority_display',
            'status', 'status_display', 'channels',
            'dashboard', 'dashboard_name', 'kpi', 'kpi_name',
            'report', 'report_name', 'pipeline', 'pipeline_name',
            'metadata', 'sent_at', 'read_at', 'delivered_at',
            'created_at', 'updated_at', 'icon', 'color', 'time_ago'
        ]
        read_only_fields = [
            'id', 'sent_at', 'read_at', 'delivered_at', 'created_at', 'updated_at'
        ]
    
    def get_time_ago(self, obj):
        from apps.core.utils import format_timesince
        return format_timesince(obj.created_at)


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de Notification"""
    
    class Meta:
        model = Notification
        fields = [
            'recipient', 'notification_type', 'title', 'message',
            'priority', 'channels', 'dashboard', 'kpi', 'report', 'pipeline', 'metadata'
        ]
    
    def create(self, validated_data):
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class NotificationChannelSerializer(serializers.ModelSerializer):
    """Sérialiseur pour NotificationChannel"""
    
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'user', 'user_name', 'channel', 'channel_display',
            'address', 'is_enabled', 'is_verified', 'last_used',
            'error_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'last_used', 'error_count', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Subscription"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_name', 'notification_type', 'notification_type_display',
            'is_enabled', 'filters', 'preferred_channels', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlertRuleSerializer(serializers.ModelSerializer):
    """Sérialiseur pour AlertRule"""
    
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    check_frequency_display = serializers.CharField(source='get_check_frequency_display', read_only=True)
    kpi_name = serializers.CharField(source='kpi.name', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'is_enabled', 'kpi', 'kpi_name',
            'condition', 'condition_display', 'threshold', 'percentage_change',
            'check_frequency', 'check_frequency_display', 'cooldown_minutes',
            'last_triggered', 'trigger_count', 'notification_channels',
            'notification_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_triggered', 'trigger_count', 'created_at', 'updated_at']


class AlertRuleCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de AlertRule"""
    
    class Meta:
        model = AlertRule
        fields = [
            'name', 'description', 'kpi', 'condition', 'threshold',
            'percentage_change', 'check_frequency', 'cooldown_minutes',
            'notification_channels', 'notification_message'
        ]


class NotificationStatsSerializer(serializers.Serializer):
    """Sérialiseur pour statistiques des notifications"""
    
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    by_type = serializers.DictField()
    by_priority = serializers.DictField()