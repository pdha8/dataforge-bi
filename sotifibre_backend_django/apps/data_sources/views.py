# apps/data_sources/views.py
"""
Vues pour l'application data_sources
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta

from apps.core.permissions import (
    IsAdmin, IsAdminOrReadOnly, 
    CanManageDataSources, CanViewDataSources
)
from apps.core.responses import (
    success_response, created_response, error_response,
    not_found_response, forbidden_response
)
from apps.core.pagination import StandardPagination
from apps.core.utils import get_client_ip, Timer

from .models import (
    DataSource, DataTable, DataQuery,
    DataSourceLog, DataSourceMetric,
    DataSourceFile,
    PowerQuery, QueryStep, StarSchema,
    DataSourceConnection
)
from .serializers import (
    DataSourceSerializer, DataSourceDetailSerializer, DataSourceCreateSerializer,
    DataSourceUpdateSerializer, DataTableSerializer, DataTableDetailSerializer,
    DataQuerySerializer, DataQueryDetailSerializer, DataQueryCreateSerializer,
    PowerQuerySerializer, QueryStepSerializer, DataSourceFileSerializer,
    DataSourceConnectionSerializer, DataSourceLogSerializer, DataSourceMetricSerializer,
    StarSchemaSerializer, StarSchemaCreateSerializer,  # ← AJOUTER
    DataSourceExecuteSerializer,
)
from .filters import (
    DataSourceFilter, DataTableFilter, DataQueryFilter,
    DataSourceLogFilter, DataSourceMetricFilter, StarSchemaFilter
)
from .services import DataSourceService, QueryService


class DataSourceViewSet(viewsets.ModelViewSet):
    """ViewSet pour DataSource"""
    
    queryset = DataSource.objects.all().select_related('owner', 'team')
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataSourceFilter
    search_fields = ['name', 'description', 'host', 'database_name']
    ordering_fields = ['name', 'created_at', 'last_sync', 'total_queries']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DataSourceDetailSerializer
        elif self.action == 'create':
            return DataSourceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DataSourceUpdateSerializer
        return DataSourceSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]
        else:
            permission_classes = [IsAuthenticated, CanViewDataSources]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        instance._request = self.request
        return instance
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Teste la connexion à la source de données"""
        source = self.get_object()
        service = DataSourceService(source)
        
        result = service.test_connection()
        
        if result['success']:
            return success_response(result, "Connexion réussie")
        else:
            return error_response(
                f"Échec de connexion: {result.get('error')}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def execute_query(self, request, pk=None):
        """Exécute une requête sur la source"""
        source = self.get_object()
        
        serializer = DataSourceExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = DataSourceService(source)
        result = service.execute_query(
            serializer.validated_data['query'],
            serializer.validated_data.get('params')
        )
        
        if result['success']:
            return success_response(result, "Requête exécutée avec succès")
        else:
            return error_response(
                f"Erreur d'exécution: {result.get('error')}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def sync_tables(self, request, pk=None):
        """Synchronise les tables de la source"""
        source = self.get_object()
        service = DataSourceService(source)
        
        result = service.sync_tables()
        
        if result['success']:
            return success_response(result, "Tables synchronisées avec succès")
        else:
            return error_response(
                f"Erreur de synchronisation: {result.get('error')}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Liste les tables de la source"""
        source = self.get_object()
        tables = source.tables.all()
        
        page = self.paginate_queryset(tables)
        if page is not None:
            serializer = DataTableSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DataTableSerializer(tables, many=True)
        return success_response(serializer.data, "Tables récupérées")
    
    @action(detail=True, methods=['get'])
    def queries(self, request, pk=None):
        """Liste les requêtes de la source"""
        source = self.get_object()
        queries = source.queries.all()
        
        page = self.paginate_queryset(queries)
        if page is not None:
            serializer = DataQuerySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DataQuerySerializer(queries, many=True)
        return success_response(serializer.data, "Requêtes récupérées")
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Liste les logs de la source"""
        source = self.get_object()
        logs = source.logs.all()
        
        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level)
        
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]
        
        serializer = DataSourceLogSerializer(logs, many=True)
        return success_response(serializer.data, "Logs récupérés")
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Liste les métriques de la source"""
        source = self.get_object()
        metrics = source.metrics.all()
        
        hours = int(request.query_params.get('hours', 24))
        if hours:
            cutoff = timezone.now() - timedelta(hours=hours)
            metrics = metrics.filter(timestamp__gte=cutoff)
        
        limit = int(request.query_params.get('limit', 100))
        metrics = metrics[:limit]
        
        serializer = DataSourceMetricSerializer(metrics, many=True)
        return success_response(serializer.data, "Métriques récupérées")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques globales"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        active = queryset.filter(status='active').count()
        error = queryset.filter(status='error').count()
        
        by_type = dict(
            queryset.values_list('source_type').annotate(count=Count('id'))
        )
        
        by_database = dict(
            queryset.exclude(database_type__isnull=True)
            .values_list('database_type')
            .annotate(count=Count('id'))
        )
        
        total_queries = queryset.aggregate(Sum('total_queries'))['total_queries__sum'] or 0
        avg_success_rate = queryset.aggregate(Avg('success_rate'))['success_rate__avg'] or 0
        
        stats_data = {
            'total': total,
            'active': active,
            'error': error,
            'by_type': by_type,
            'by_database': by_database,
            'total_queries': total_queries,
            'avg_success_rate': round(avg_success_rate, 1),
        }
        
        return success_response(stats_data, "Statistiques récupérées")


class DataTableViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour DataTable (lecture seule)"""
    
    queryset = DataTable.objects.all().select_related('data_source')
    serializer_class = DataTableSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataTableFilter
    search_fields = ['name', 'schema', 'description']
    ordering_fields = ['name', 'row_count', 'last_updated']
    ordering = ['data_source', 'schema', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DataTableDetailSerializer
        return DataTableSerializer
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Aperçu des données de la table"""
        table = self.get_object()
        
        service = DataSourceService(table.data_source)
        result = service.execute_query(f"SELECT * FROM {table.full_name} LIMIT 10")
        
        if result['success']:
            return success_response(result, "Aperçu des données")
        else:
            return error_response(
                f"Erreur: {result.get('error')}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='table-schema')
    def get_schema(self, request, pk=None):
        """Schéma de la table"""
        table = self.get_object()
        
        schema_data = {
            'name': table.full_name,
            'columns': table.columns,
            'primary_key': table.primary_key,
            'indexes': table.indexes,
            'foreign_keys': table.foreign_keys,
            'row_count': table.row_count,
            'size_bytes': table.size_bytes,
        }
        
        return success_response(schema_data, "Schéma récupéré")


class DataQueryViewSet(viewsets.ModelViewSet):
    """ViewSet pour DataQuery"""
    
    queryset = DataQuery.objects.all().select_related('data_source', 'created_by')
    serializer_class = DataQuerySerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataQueryFilter
    search_fields = ['name', 'description', 'query_text']
    ordering_fields = ['name', 'execution_count', 'last_executed', 'created_at']
    ordering = ['-is_favorite', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DataQueryDetailSerializer
        elif self.action == 'create':
            return DataQueryCreateSerializer
        return DataQuerySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]
        else:
            permission_classes = [IsAuthenticated, CanViewDataSources]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        return instance
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute la requête"""
        query = self.get_object()
        
        if not query.is_public and query.created_by != request.user and not request.user.is_admin:
            return forbidden_response(
                "Vous n'avez pas accès à cette requête",
                required_permission="is_owner_or_admin"
            )
        
        service = QueryService(query)
        result = service.execute(request.data.get('params'))
        
        if result['success']:
            return success_response(result, "Requête exécutée avec succès")
        else:
            return error_response(
                f"Erreur d'exécution: {result.get('error')}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Ajoute/retire des favoris"""
        query = self.get_object()
        query.is_favorite = not query.is_favorite
        query.save()
        
        status_msg = "ajoutée aux" if query.is_favorite else "retirée des"
        return success_response(
            {'is_favorite': query.is_favorite},
            f"Requête {status_msg} favoris"
        )
    
    @action(detail=True, methods=['post'])
    def clear_cache(self, request, pk=None):
        """Vide le cache de la requête"""
        query = self.get_object()
        query.clear_cache()
        
        return success_response(None, "Cache vidé avec succès")


class StarSchemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour StarSchema - Schémas en étoile
    """
    
    queryset = StarSchema.objects.all().select_related('fact_table', 'owner', 'team')
    serializer_class = StarSchemaSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StarSchemaFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'query_count']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StarSchemaCreateSerializer
        return StarSchemaSerializer
    
    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        return instance
    
    @action(detail=True, methods=['get'])
    def generate_sql(self, request, pk=None):
        """Génère la requête SQL pour le schéma en étoile"""
        schema = self.get_object()
        
        try:
            sql = schema.generate_query()
            
            # Incrémenter le compteur de requêtes
            schema.query_count += 1
            schema.last_queried_at = timezone.now()
            schema.save(update_fields=['query_count', 'last_queried_at'])
            
            return success_response({
                'sql': sql,
                'fact_table': schema.fact_table.full_name,
                'dimension_tables': [dt.full_name for dt in schema.dimension_tables.all()],
                'measures': schema.measures,
                'dimensions': schema.dimension_columns
            }, "Requête SQL générée avec succès")
            
        except Exception as e:
            return error_response(f"Erreur de génération: {str(e)}", status_code=500)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute la requête du schéma en étoile"""
        schema = self.get_object()
        
        try:
            sql = schema.generate_query()
            
            # Exécuter la requête via le service de la source de données
            service = DataSourceService(schema.fact_table.data_source)
            result = service.execute_query(sql)
            
            if result['success']:
                # Incrémenter le compteur
                schema.query_count += 1
                schema.last_queried_at = timezone.now()
                schema.save(update_fields=['query_count', 'last_queried_at'])
                
                return success_response(result, "Requête exécutée avec succès")
            else:
                return error_response(
                    f"Erreur d'exécution: {result.get('error')}",
                    status_code=500
                )
                
        except Exception as e:
            return error_response(f"Erreur: {str(e)}", status_code=500)
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Aperçu des données du schéma en étoile (LIMIT 10)"""
        schema = self.get_object()
        
        try:
            sql = schema.generate_query()
            sql += " LIMIT 10"
            
            service = DataSourceService(schema.fact_table.data_source)
            result = service.execute_query(sql)
            
            if result['success']:
                return success_response(result, "Aperçu des données")
            else:
                return error_response(
                    f"Erreur: {result.get('error')}",
                    status_code=500
                )
                
        except Exception as e:
            return error_response(f"Erreur: {str(e)}", status_code=500)

class DataSourceLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour DataSourceLog (lecture seule)"""
    
    queryset = DataSourceLog.objects.all().select_related('data_source')
    serializer_class = DataSourceLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DataSourceLogFilter
    ordering_fields = ['created_at', 'level']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des logs"""
        queryset = self.get_queryset()
        
        last_24h = timezone.now() - timedelta(hours=24)
        recent = queryset.filter(created_at__gte=last_24h)
        
        stats = {
            'total': queryset.count(),
            'last_24h': recent.count(),
            'by_level': dict(recent.values_list('level').annotate(count=Count('id'))),
        }
        
        return success_response(stats, "Statistiques des logs")


class DataSourceMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour DataSourceMetric (lecture seule)"""
    
    queryset = DataSourceMetric.objects.all().select_related('data_source')
    serializer_class = DataSourceMetricSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DataSourceMetricFilter
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Dernières métriques pour chaque source"""
        source_id = request.query_params.get('source')
        
        if source_id:
            metrics = DataSourceMetric.objects.filter(
                data_source_id=source_id
            ).order_by('-timestamp')[:1]
            serializer = self.get_serializer(metrics, many=True)
            return success_response(serializer.data, "Dernière métrique")
        
        # Récupérer la dernière métrique pour chaque source
        from django.db.models import Max
        
        latest_ids = DataSourceMetric.objects.values('data_source').annotate(
            latest=Max('id')
        ).values_list('latest', flat=True)
        
        latest_metrics = DataSourceMetric.objects.filter(id__in=latest_ids)
        
        page = self.paginate_queryset(latest_metrics)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(latest_metrics, many=True)
        return success_response(serializer.data, "Dernières métriques")

# apps/data_sources/views.py - AJOUTER À LA FIN DU FICHIER

class DataSourceFileViewSet(viewsets.ModelViewSet):
    """ViewSet pour DataSourceFile - Gestion des fichiers uploadés"""
    
    queryset = DataSourceFile.objects.all().select_related('data_source', 'uploaded_by')
    serializer_class = DataSourceFileSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['original_name', 'notes']
    ordering_fields = ['created_at', 'file_size']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Crée un fichier avec l'utilisateur connecté"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Traite le fichier (analyse, détection schéma)"""
        file_obj = self.get_object()
        
        # Logique de traitement
        try:
            import pandas as pd
            from io import BytesIO
            
            # Lire le fichier
            if file_obj.file.name.endswith('.csv'):
                df = pd.read_csv(file_obj.file, encoding=file_obj.encoding or 'utf-8')
            elif file_obj.file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_obj.file, sheet_name=file_obj.sheet_name or 0)
            elif file_obj.file.name.endswith('.json'):
                df = pd.read_json(file_obj.file)
            else:
                return error_response(f"Format non supporté: {file_obj.file.name}")
            
            # Mettre à jour les informations
            file_obj.row_count = len(df)
            file_obj.column_count = len(df.columns)
            file_obj.preview_data = df.head(10).to_dict('records')
            file_obj.schema = {col: str(df[col].dtype) for col in df.columns}
            file_obj.process_status = 'completed'
            file_obj.processed_at = timezone.now()
            file_obj.save()
            
            return success_response({
                'row_count': file_obj.row_count,
                'column_count': file_obj.column_count,
                'columns': list(df.columns),
                'preview': file_obj.preview_data
            }, "Fichier traité avec succès")
            
        except Exception as e:
            file_obj.process_status = 'failed'
            file_obj.processing_errors.append({'error': str(e), 'timestamp': timezone.now().isoformat()})
            file_obj.save()
            return error_response(f"Erreur de traitement: {str(e)}", status_code=500)
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Aperçu des données du fichier"""
        file_obj = self.get_object()
        
        if not file_obj.preview_data:
            return error_response("Aucune donnée d'aperçu disponible. Traitez d'abord le fichier.")
        
        return success_response({
            'preview': file_obj.preview_data,
            'schema': file_obj.schema,
            'row_count': file_obj.row_count,
            'column_count': file_obj.column_count
        }, "Aperçu récupéré")


class PowerQueryViewSet(viewsets.ModelViewSet):
    """ViewSet pour PowerQuery - Transformations M"""
    
    queryset = PowerQuery.objects.all().select_related('data_source', 'created_by')
    serializer_class = PowerQuerySerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'm_code']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def perform_create(self, serializer):
        """Crée un Power Query"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def steps(self, request, pk=None):
        """Liste les étapes du Power Query"""
        power_query = self.get_object()
        steps = power_query.steps.all().order_by('step_order')
        
        serializer = QueryStepSerializer(steps, many=True)
        return success_response(serializer.data, "Étapes récupérées")
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute le Power Query"""
        power_query = self.get_object()
        
        try:
            # Ici, logique d'exécution du code M
            # Pour l'instant, simulation
            return success_response({
                'executed': True,
                'steps_count': power_query.query_steps.count(),
                'result_row_count': power_query.result_row_count
            }, "Power Query exécuté avec succès")
        except Exception as e:
            return error_response(f"Erreur d'exécution: {str(e)}", status_code=500)


class DataSourceConnectionViewSet(viewsets.ModelViewSet):
    """ViewSet pour DataSourceConnection"""
    
    queryset = DataSourceConnection.objects.all().select_related('data_source')
    serializer_class = DataSourceConnectionSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['host', 'database_name']
    ordering = ['data_source__name']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Teste la connexion"""
        connection = self.get_object()
        
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, text
            
            # Construire la chaîne de connexion
            if connection.connection_string:
                conn_str = connection.connection_string
            else:
                conn_str = f"{connection.data_source.database_type}://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database_name}"
            
            engine = create_engine(conn_str, connect_args={'connect_timeout': 10})
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    connection.is_connected = True
                    connection.last_connected = timezone.now()
                    connection.connection_test_result = {'success': True, 'message': 'Connexion réussie'}
                    connection.save()
                    
                    return success_response({'success': True}, "Connexion réussie")
            
            return error_response("La requête de test a échoué", status_code=500)
            
        except Exception as e:
            connection.is_connected = False
            connection.connection_test_result = {'success': False, 'error': str(e)}
            connection.save()
            return error_response(f"Échec de connexion: {str(e)}", status_code=500)
