# apps/etl_engine/serializers.py
"""
Sérialiseurs pour l'application etl_engine
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import models
from .models import (
    ETLPipeline, Transformation, ExecutionLog, 
    TargetSchema, SourceSchema, PipelineNotification
)
from apps.users.serializers import UserMinimalSerializer
from apps.data_sources.serializers import DataSourceSerializer


# ============================================================================
# BASE SERIALIZER AVEC GESTION DES DATES
# ============================================================================

class BaseETLSerializer(serializers.ModelSerializer):
    """Classe de base pour tous les sérialiseurs ETL"""
    
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
# PIPELINE ETL
# ============================================================================

class TransformationSerializer(BaseETLSerializer):
    """Sérialiseur pour Transformation"""
    
    transformation_type_display = serializers.CharField(
        source='get_transformation_type_display', read_only=True
    )
    
    class Meta:
        model = Transformation
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'execution_count',
            'avg_duration_ms', 'last_duration_ms', 'error_count', 'last_error'
        ]


class TargetSchemaSerializer(BaseETLSerializer):
    """Sérialiseur pour TargetSchema"""
    
    insert_strategy_display = serializers.CharField(
        source='get_insert_strategy_display', read_only=True
    )
    partition_type_display = serializers.CharField(
        source='get_partition_type_display', read_only=True
    )
    
    class Meta:
        model = TargetSchema
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SourceSchemaSerializer(BaseETLSerializer):
    """Sérialiseur pour SourceSchema"""
    
    class Meta:
        model = SourceSchema
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_value']


class PipelineNotificationSerializer(BaseETLSerializer):
    """Sérialiseur pour PipelineNotification"""
    
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    
    class Meta:
        model = PipelineNotification
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ETLPipelineSerializer(BaseETLSerializer):
    """Sérialiseur pour ETLPipeline"""
    
    pipeline_type_display = serializers.CharField(
        source='get_pipeline_type_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    error_strategy_display = serializers.CharField(
        source='get_error_strategy_display', read_only=True
    )
    processing_mode_display = serializers.CharField(
        source='get_processing_mode_display', read_only=True
    )
    schedule_frequency_display = serializers.CharField(
        source='get_schedule_frequency_display', read_only=True
    )
    
    success_rate = serializers.FloatField(read_only=True)
    health_status = serializers.CharField(read_only=True)
    health_badge = serializers.SerializerMethodField()
    
    source_name = serializers.CharField(source='source.name', read_only=True)
    source_type = serializers.CharField(source='source.source_type', read_only=True)
    target_name = serializers.CharField(source='target.name', read_only=True)
    target_type = serializers.CharField(source='target.source_type', read_only=True)
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ETLPipeline
        fields = [
            'id', 'name', 'description', 'pipeline_type', 'pipeline_type_display',
            'status', 'status_display', 'version',
            'source', 'source_name', 'source_type', 'source_endpoint_type',
            'source_config', 'target', 'target_name', 'target_type',
            'target_endpoint_type', 'target_config',
            'transformations', 'transformation_order',
            'schedule_enabled', 'schedule_frequency', 'schedule_frequency_display',
            'schedule_cron', 'last_execution', 'next_execution',
            'batch_size', 'timeout_seconds', 'max_errors', 'error_strategy',
            'error_strategy_display', 'processing_mode', 'processing_mode_display',
            'retry_policy', 'dependencies', 'dependency_graph',
            'notifications_enabled', 'notification_channels', 'notify_on_success',
            'notify_on_failure', 'notify_on_start',
            'execution_count', 'success_count', 'failure_count', 'success_rate',
            'avg_duration_seconds', 'last_duration_seconds', 'total_rows_processed',
            'data_quality_score', 'validation_rules', 'health_status', 'health_badge',
            'tags', 'category', 'priority',
            'owner', 'owner_name', 'team', 'team_name', 'created_by', 'created_by_name',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'last_execution', 'next_execution',
            'execution_count', 'success_count', 'failure_count', 'success_rate',
            'avg_duration_seconds', 'last_duration_seconds', 'total_rows_processed',
            'data_quality_score'
        ]
    
    def get_health_badge(self, obj):
        badges = {
            'critical': '🔴',
            'warning': '🟠',
            'poor': '🟡',
            'fair': '🟡',
            'good': '🟢',
        }
        return badges.get(obj.health_status, '⚪')


class ETLPipelineDetailSerializer(ETLPipelineSerializer):
    """Sérialiseur détaillé pour ETLPipeline"""
    
    transformations_list = TransformationSerializer(
        source='transformation_list', many=True, read_only=True
    )
    target_schema_detail = TargetSchemaSerializer(source='target_schema', read_only=True)
    source_schema_detail = SourceSchemaSerializer(source='source_schema', read_only=True)
    notifications_detail = PipelineNotificationSerializer(
        source='notifications', many=True, read_only=True
    )
    dependencies_detail = serializers.SerializerMethodField()
    recent_executions = serializers.SerializerMethodField()
    
    class Meta(ETLPipelineSerializer.Meta):
        fields = ETLPipelineSerializer.Meta.fields + [
            'transformations_list', 'target_schema_detail', 'source_schema_detail',
            'notifications_detail', 'dependencies_detail', 'recent_executions'
        ]
    
    def get_dependencies_detail(self, obj):
        return [
            {'id': dep.id, 'name': dep.name, 'status': dep.status}
            for dep in obj.dependencies.all()
        ]
    
    def get_recent_executions(self, obj):
        executions = obj.executions.all()[:10]
        return ExecutionLogSerializer(executions, many=True).data


class ETLPipelineCreateSerializer(BaseETLSerializer):
    """Sérialiseur pour création de pipeline"""
    
    class Meta:
        model = ETLPipeline
        fields = [
            'id', 'name', 'description', 'pipeline_type', 'source', 'target',
            'source_endpoint_type', 'source_config', 'target_endpoint_type',
            'target_config', 'transformations', 'transformation_order',
            'schedule_enabled', 'schedule_frequency', 'schedule_cron',
            'batch_size', 'timeout_seconds', 'max_errors', 'error_strategy',
            'processing_mode', 'retry_policy', 'notifications_enabled',
            'notification_channels', 'notify_on_success', 'notify_on_failure',
            'notify_on_start', 'validation_rules', 'tags', 'category', 'priority',
            'owner', 'team', 'notes'
        ]
        read_only_fields = ['id']


class ETLPipelineUpdateSerializer(BaseETLSerializer):
    """Sérialiseur pour mise à jour de pipeline"""
    
    class Meta:
        model = ETLPipeline
        fields = [
            'name', 'description', 'status', 'schedule_enabled', 'schedule_frequency',
            'schedule_cron', 'batch_size', 'timeout_seconds', 'max_errors',
            'error_strategy', 'processing_mode', 'retry_policy', 'notifications_enabled',
            'notification_channels', 'notify_on_success', 'notify_on_failure',
            'notify_on_start', 'validation_rules', 'tags', 'category', 'priority',
            'notes'
        ]


# ============================================================================
# TRANSFORMATION
# ============================================================================

class TransformationDetailSerializer(TransformationSerializer):
    """Sérialiseur détaillé pour Transformation"""
    
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    
    class Meta(TransformationSerializer.Meta):
        # Redéfinir explicitement les champs car le parent utilise '__all__'
        fields = [
            'id', 'pipeline', 'pipeline_name', 'order', 'name', 'description',
            'transformation_type', 'transformation_type_display', 'config',
            'custom_code', 'sql_code', 'is_enabled', 'is_critical',
            'execution_count', 'avg_duration_ms', 'last_duration_ms',
            'error_count', 'last_error', 'created_at', 'updated_at'
        ]


class TransformationCreateSerializer(BaseETLSerializer):
    """Sérialiseur pour création de transformation"""
    
    class Meta:
        model = Transformation
        fields = [
            'pipeline', 'order', 'name', 'description', 'transformation_type',
            'config', 'custom_code', 'sql_code', 'is_enabled', 'is_critical'
        ]


# ============================================================================
# EXÉCUTION
# ============================================================================

class ExecutionLogSerializer(BaseETLSerializer):
    """Sérialiseur pour ExecutionLog"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    triggered_by_display = serializers.CharField(source='get_triggered_by_display', read_only=True)
    pipeline_name = serializers.CharField(source='pipeline.name', read_only=True)
    triggered_by_user_name = serializers.CharField(
        source='triggered_by_user.get_full_name', read_only=True
    )
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ExecutionLog
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'execution_id', 'started_at',
            'completed_at', 'duration_seconds', 'rows_read', 'rows_written',
            'rows_errors'
        ]
    
    def get_duration_formatted(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            elif obj.duration_seconds < 3600:
                minutes = obj.duration_seconds / 60
                return f"{minutes:.1f}m"
            else:
                hours = obj.duration_seconds / 3600
                return f"{hours:.1f}h"
        return "N/A"


class ExecutionLogDetailSerializer(ExecutionLogSerializer):
    """Sérialiseur détaillé pour ExecutionLog"""
    
    class Meta(ExecutionLogSerializer.Meta):
        # Redéfinir explicitement les champs car le parent utilise '__all__'
        fields = [
            'id', 'pipeline', 'pipeline_name', 'execution_id', 'status', 'status_display',
            'started_at', 'completed_at', 'duration_seconds', 'duration_formatted',
            'rows_read', 'rows_written', 'rows_errors', 'triggered_by', 'triggered_by_display',
            'triggered_by_user', 'triggered_by_user_name', 'result_summary',
            'error_message', 'error_traceback', 'execution_metadata', 'transformation_logs',
            'created_at', 'updated_at'
        ]


class ExecutionTriggerSerializer(serializers.Serializer):
    """Sérialiseur pour déclencher une exécution"""
    
    params = serializers.JSONField(required=False, help_text="Paramètres d'exécution")
    wait = serializers.BooleanField(
        required=False, default=False,
        help_text="Attendre la fin de l'exécution"
    )


# ============================================================================
# STATISTIQUES
# ============================================================================

class ETLPipelineStatsSerializer(serializers.Serializer):
    """Statistiques des pipelines ETL"""
    
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    error = serializers.IntegerField()
    by_type = serializers.DictField()
    total_executions = serializers.IntegerField()
    avg_duration_seconds = serializers.FloatField()
    avg_success_rate = serializers.FloatField()


class ExecutionStatsSerializer(serializers.Serializer):
    """Statistiques des exécutions"""
    
    period = serializers.CharField()
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    failed = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_duration = serializers.FloatField()
    by_status = serializers.DictField()
    timeline = serializers.ListField()