# apps/data_sources/serializers.py
"""
Sérialiseurs pour l'application data_sources - Version optimisée
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    DataSource, DataTable, DataQuery, PowerQuery, QueryStep,
    DataSourceFile, DataSourceConnection, StarSchema,
    DataSourceLog, DataSourceMetric, DataSourceHistory
)
from apps.users.serializers import UserMinimalSerializer


class DataSourceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataSource"""
    
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    database_type_display = serializers.CharField(source='get_database_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_badge = serializers.SerializerMethodField()
    sync_frequency_display = serializers.CharField(source='get_sync_frequency_display', read_only=True)
    
    success_rate = serializers.FloatField(read_only=True)
    is_connected = serializers.BooleanField(read_only=True)
    health_status = serializers.CharField(read_only=True)
    health_badge = serializers.SerializerMethodField()
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'description', 'source_type', 'source_type_display',
            'database_type', 'database_type_display', 'status', 'status_display',
            'status_badge', 'health_status', 'health_badge', 'host', 'port', 
            'database_name', 'schema_name', 'sync_frequency', 'sync_frequency_display',
            'auto_refresh_enabled', 'last_sync', 'last_sync_status', 'success_rate',
            'is_connected', 'total_queries', 'avg_query_time_ms', 'data_quality_score',
            'error_count', 'consecutive_failures', 'is_validated', 'is_public',
            'owner', 'owner_name', 'owner_email', 'team', 'team_name', 'tags', 
            'category', 'business_domain', 'owner_team', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_queries', 'successful_queries',
            'failed_queries', 'avg_query_time_ms', 'last_query_time', 'data_quality_score',
            'error_count', 'consecutive_failures'
        ]
    
    def get_status_badge(self, obj):
        badges = {
            'active': '✅',
            'error': '❌',
            'testing': '🔍',
            'inactive': '⏸️',
            'configuring': '⚙️',
            'draft': '📝',
            'archived': '📦',
            'deprecated': '⚠️',
        }
        return badges.get(obj.status, '❓')
    
    def get_health_badge(self, obj):
        badges = {
            'critical': '🔴',
            'warning': '🟠',
            'fair': '🟡',
            'good': '🟢',
        }
        return badges.get(obj.health_status, '⚪')


class DataSourceDetailSerializer(DataSourceSerializer):
    """Sérialiseur détaillé pour DataSource"""
    
    tables_count = serializers.IntegerField(read_only=True)
    queries_count = serializers.IntegerField(read_only=True)
    files_count = serializers.IntegerField(read_only=True)
    recent_logs = serializers.SerializerMethodField()
    recent_metrics = serializers.SerializerMethodField()
    connection_detail = serializers.SerializerMethodField()
    
    class Meta(DataSourceSerializer.Meta):
        fields = DataSourceSerializer.Meta.fields + [
            'connection_string', 'username', 'api_url', 'api_endpoint', 'api_headers',
            'api_params', 'file_path', 'file_url', 'file_encoding', 'file_delimiter',
            'cloud_provider', 'bucket_name', 'object_key', 'region', 'streaming_topic',
            'streaming_broker', 'auth_type', 'auth_token', 'api_key', 'api_key_header',
            'use_ssl', 'ssl_certificate', 'ssl_mode', 'oauth2_client_id', 'oauth2_client_secret',
            'oauth2_token_url', 'use_credential_vault', 'notes', 'schema_info', 'sample_data',
            'metadata', 'documentation_url', 'support_contact', 'icon', 'color',
            'tables_count', 'queries_count', 'files_count', 'recent_logs', 'recent_metrics',
            'connection_detail'
        ]
    
    def get_recent_logs(self, obj):
        logs = obj.logs.all()[:10]
        return DataSourceLogSerializer(logs, many=True).data
    
    def get_recent_metrics(self, obj):
        metrics = obj.metrics.all()[:10]
        return DataSourceMetricSerializer(metrics, many=True).data
    
    def get_connection_detail(self, obj):
        if hasattr(obj, 'connection'):
            return DataSourceConnectionSerializer(obj.connection).data
        return None


class DataSourceCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de source"""
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'description', 'source_type', 'database_type',
            'connection_string', 'host', 'port', 'database_name', 'schema_name',
            'username', 'password', 'api_url', 'api_endpoint', 'api_headers',
            'api_params', 'file_path', 'file_url', 'file_encoding', 'file_delimiter',
            'cloud_provider', 'bucket_name', 'object_key', 'region', 'streaming_topic',
            'streaming_broker', 'auth_type', 'auth_token', 'api_key', 'api_key_header',
            'use_ssl', 'ssl_certificate', 'sync_frequency', 'auto_refresh_enabled',
            'tags', 'category', 'business_domain', 'owner_team'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Le mot de passe sera chiffré dans le service
        return super().create(validated_data)


class DataSourceUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mise à jour de source"""
    
    class Meta:
        model = DataSource
        fields = [
            'name', 'description', 'status', 'sync_frequency', 'auto_refresh_enabled',
            'connection_string', 'host', 'port', 'database_name', 'schema_name',
            'username', 'password', 'api_url', 'api_endpoint', 'api_headers',
            'api_params', 'file_path', 'file_url', 'tags', 'category', 'notes',
            'is_validated', 'is_public'
        ]


# apps/data_sources/serializers.py - CORRIGER DataTableSerializer

class DataTableSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataTable"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    data_source_type = serializers.CharField(source='data_source.source_type', read_only=True)
    full_name = serializers.CharField(read_only=True)
    column_count = serializers.IntegerField(read_only=True)
    size_mb = serializers.SerializerMethodField()  # ← AJOUTER CECI (méthode, pas champ)
    
    class Meta:
        model = DataTable
        fields = [
            'id', 'data_source', 'data_source_name', 'data_source_type', 'name', 'schema',
            'full_name', 'description', 'row_count', 'size_bytes', 'size_mb',  # ← size_mb reste dans fields
            'columns', 'column_count', 'primary_key', 'indexes', 'foreign_keys',
            'is_partitioned', 'partition_column', 'partition_count', 'last_updated',
            'last_analyzed', 'update_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_size_mb(self, obj):
        """Calcule la taille en MB"""
        if obj.size_bytes:
            return round(obj.size_bytes / (1024 * 1024), 2)
        return 0


class DataTableDetailSerializer(DataTableSerializer):
    """Sérialiseur détaillé pour DataTable"""
    
    class Meta(DataTableSerializer.Meta):
        fields = DataTableSerializer.Meta.fields + ['catalog']


# apps/data_sources/serializers.py - Ajouter si manquant

class DataQuerySerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataQuery"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    query_type_display = serializers.CharField(source='get_query_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    time_since_last_exec = serializers.SerializerMethodField()
    
    class Meta:
        model = DataQuery
        fields = [
            'id', 'data_source', 'data_source_name', 'name', 'description',
            'query_type', 'query_type_display', 'query_text', 'parameters',
            'is_favorite', 'is_public', 'tags', 'execution_count',
            'avg_execution_time_ms', 'last_executed', 'time_since_last_exec',
            'is_cached', 'cache_ttl', 'cached_at',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'execution_count', 'avg_execution_time_ms',
            'last_executed', 'cached_at', 'created_at', 'updated_at'
        ]
    
    def get_time_since_last_exec(self, obj):
        if obj.last_executed:
            delta = timezone.now() - obj.last_executed
            if delta.days > 0:
                return f"{delta.days}j"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}h"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60}m"
            return "maintenant"
        return "jamais"


class DataQueryDetailSerializer(DataQuerySerializer):
    """Sérialiseur détaillé pour DataQuery"""
    
    cached_result = serializers.JSONField(read_only=True)
    
    class Meta(DataQuerySerializer.Meta):
        fields = DataQuerySerializer.Meta.fields + ['cached_result']


class DataQueryCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de requête"""

    class Meta:
        model = DataQuery
        fields = [
            'id', 'data_source', 'name', 'description', 'query_type',
            'query_text', 'parameters', 'is_favorite', 'is_public',
            'tags', 'cache_ttl', 'is_cached'
        ]
        read_only_fields = ['id']


# apps/data_sources/serializers.py - CORRIGER PowerQuerySerializer
class PowerQuerySerializer(serializers.ModelSerializer):
    """Sérialiseur pour PowerQuery"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Champs datetime avec gestion des chaînes vides
    last_executed = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    
    class Meta:
        model = PowerQuery
        fields = [
            'id', 'data_source', 'data_source_name', 'name', 'description',
            'query_steps', 'm_code', 'sql_query', 'output_schema',
            'is_enabled', 'is_cached', 'cache_ttl_minutes',
            'last_executed', 'execution_time_ms', 'preview_result',
            'result_row_count', 'execution_count', 'error_count',
            'created_by', 'created_by_name', 'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'execution_count', 
            'error_count', 'last_executed', 'execution_time_ms'
        ]
    
    def get_last_executed(self, obj):
        """Récupère last_executed en gérant les valeurs nulles"""
        if obj.last_executed:
            return obj.last_executed.isoformat()
        return None
    
    def get_created_at(self, obj):
        """Récupère created_at"""
        if obj.created_at:
            return obj.created_at.isoformat()
        return None
    
    def get_updated_at(self, obj):
        """Récupère updated_at"""
        if obj.updated_at:
            return obj.updated_at.isoformat()
        return None


class QueryStepSerializer(serializers.ModelSerializer):
    """Sérialiseur pour QueryStep"""
    
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    
    class Meta:
        model = QueryStep
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class DataSourceFileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataSourceFile"""

    data_source_name = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    process_status_display = serializers.CharField(source='get_process_status_display', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    is_processed = serializers.BooleanField(read_only=True)

    # original_name est auto-rempli depuis le fichier uploadé — pas requis dans le formulaire
    original_name = serializers.CharField(required=False, default='', allow_blank=True)

    created_at  = serializers.SerializerMethodField()
    updated_at  = serializers.SerializerMethodField()
    processed_at = serializers.SerializerMethodField()
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = DataSourceFile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_hash', 'file_size']

    def get_data_source_name(self, obj):
        return obj.data_source.name if obj.data_source else None

    def get_file_size_mb(self, obj):
        return obj.file_size_mb

    def get_created_at(self, obj):
        return obj.created_at.isoformat() if obj.created_at else None

    def get_updated_at(self, obj):
        return obj.updated_at.isoformat() if obj.updated_at else None

    def get_processed_at(self, obj):
        return obj.processed_at.isoformat() if obj.processed_at else None

    def get_uploaded_at(self, obj):
        return obj.created_at.isoformat() if obj.created_at else None


class DataSourceConnectionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataSourceConnection"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    
    class Meta:
        model = DataSourceConnection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_connected', 'last_connected', 'latency_ms']


# apps/data_sources/serializers.py - AJOUTER

class StarSchemaSerializer(serializers.ModelSerializer):
    """Sérialiseur pour StarSchema"""
    
    fact_table_name = serializers.CharField(source='fact_table.full_name', read_only=True)
    fact_table_data_source = serializers.CharField(source='fact_table.data_source.name', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    dimension_tables_count = serializers.IntegerField(read_only=True)
    dimension_tables_detail = serializers.SerializerMethodField()
    measures_count = serializers.IntegerField(read_only=True)
    generated_sql = serializers.SerializerMethodField()
    
    class Meta:
        model = StarSchema
        fields = [
            'id', 'name', 'description', 'fact_table', 'fact_table_name',
            'fact_table_data_source', 'dimension_tables', 'dimension_tables_count',
            'dimension_tables_detail', 'fact_columns', 'dimension_columns',
            'measures', 'measures_count', 'relationships', 'grain',
            'owner', 'owner_name', 'team', 'team_name', 'tags',
            'is_active', 'is_public', 'query_count', 'last_queried_at',
            'generated_sql', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'query_count', 'last_queried_at'
        ]
    
    def get_dimension_tables_detail(self, obj):
        return [
            {
                'id': dt.id,
                'name': dt.full_name,
                'data_source': dt.data_source.name
            }
            for dt in obj.dimension_tables.all()
        ]
    
    def get_measures_count(self, obj):
        return obj.measures_count
    
    def get_generated_sql(self, obj):
        return obj.generate_query()[:500] + "..." if len(obj.generate_query()) > 500 else obj.generate_query()


class StarSchemaCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création de schéma en étoile"""
    
    class Meta:
        model = StarSchema
        fields = [
            'name', 'description', 'fact_table', 'dimension_tables',
            'fact_columns', 'dimension_columns', 'measures',
            'relationships', 'grain', 'owner', 'team', 'tags',
            'is_active', 'is_public'
        ]

class DataSourceLogSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataSourceLog"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    level_icon = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = DataSourceLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
    
    def get_level_icon(self, obj):
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'debug': '🐛',
        }
        return icons.get(obj.level, '📝')
    
    def get_time_ago(self, obj):
        from apps.core.utils import format_timesince
        return format_timesince(obj.created_at, default="à l'instant")


class DataSourceMetricSerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataSourceMetric"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    
    class Meta:
        model = DataSourceMetric
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


class DataSourceHistorySerializer(serializers.ModelSerializer):
    """Sérialiseur pour DataSourceHistory"""
    
    data_source_name = serializers.CharField(source='data_source.name', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = DataSourceHistory
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class DataSourceTestSerializer(serializers.Serializer):
    """Sérialiseur pour test de connexion"""
    pass


class DataSourceExecuteSerializer(serializers.Serializer):
    """Sérialiseur pour exécution de requête"""
    
    query = serializers.CharField(required=True, help_text="Requête à exécuter")
    params = serializers.JSONField(required=False, help_text="Paramètres de la requête")


class DataSourceSyncSerializer(serializers.Serializer):
    """Sérialiseur pour synchronisation"""
    
    force = serializers.BooleanField(required=False, default=False)


class DataSourceStatsSerializer(serializers.Serializer):
    """Statistiques des sources de données"""
    
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    error = serializers.IntegerField()
    by_type = serializers.DictField()
    by_database = serializers.DictField()
    total_queries = serializers.IntegerField()
    avg_success_rate = serializers.FloatField()
    avg_quality_score = serializers.FloatField()