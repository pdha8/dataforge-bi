"""
Vues pour l'application data_warehouse
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated  # ← Import from DRF only
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from apps.core.permissions import CanManageDataSources, CanViewDataSources  # ← Remove IsAuthenticated from here
from apps.core.responses import success_response, created_response, error_response, forbidden_response
from apps.core.pagination import StandardPagination

from .models import (
    DataWarehouseSchema, DataWarehouseTable, FactTable, DimensionTable,
    StarSchema, Measure, DimensionAttribute, AggregationTable,
    DataWarehouseLog, DataWarehouseMetric
)
from .serializers import (
    DataWarehouseSchemaSerializer, DataWarehouseSchemaCreateSerializer,
    DataWarehouseTableSerializer, FactTableSerializer, DimensionTableSerializer,
    DataWarehouseTableCreateSerializer, MeasureSerializer, MeasureCreateSerializer,
    DimensionAttributeSerializer, DimensionAttributeCreateSerializer,
    StarSchemaSerializer, StarSchemaCreateSerializer, AggregationTableSerializer,
    DataWarehouseLogSerializer, DataWarehouseMetricSerializer,
    DataWarehouseStatsSerializer
)
from .filters import (
    DataWarehouseSchemaFilter, DataWarehouseTableFilter, FactTableFilter,
    DimensionTableFilter, StarSchemaFilter, MeasureFilter,
    DimensionAttributeFilter, AggregationTableFilter
)
from .services import StarSchemaService, DataWarehouseService


class DataWarehouseSchemaViewSet(viewsets.ModelViewSet):
    """ViewSet pour DataWarehouseSchema"""
    
    queryset = DataWarehouseSchema.objects.all()
    serializer_class = DataWarehouseSchemaSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataWarehouseSchemaFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'table_count', 'size_bytes']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DataWarehouseSchemaCreateSerializer
        return DataWarehouseSchemaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(
            DataWarehouseSchemaSerializer(serializer.instance, context=self.get_serializer_context()).data,
            "Schéma créé avec succès"
        )

    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Liste les tables du schéma"""
        schema = self.get_object()
        tables = schema.tables.all()
        
        page = self.paginate_queryset(tables)
        if page is not None:
            serializer = DataWarehouseTableSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DataWarehouseTableSerializer(tables, many=True)
        return success_response(serializer.data, "Tables récupérées")
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Statistiques du schéma"""
        schema = self.get_object()
        
        stats = {
            'name': schema.name,
            'table_count': schema.table_count,
            'size_mb': schema.size_mb,
            'fact_tables': schema.tables.filter(table_type='fact').count(),
            'dimension_tables': schema.tables.filter(table_type='dimension').count(),
            'aggregate_tables': schema.tables.filter(table_type='aggregate').count(),
            'last_analyzed': schema.last_analyzed,
        }
        
        return success_response(stats, "Statistiques du schéma")


class DataWarehouseTableViewSet(viewsets.ModelViewSet):
    """ViewSet pour DataWarehouseTable"""
    
    queryset = DataWarehouseTable.objects.all().select_related('schema', 'source_table', 'source_pipeline', 'technical_owner')
    serializer_class = DataWarehouseTableSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DataWarehouseTableFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'row_count', 'size_bytes', 'created_at']
    ordering = ['schema', 'name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DataWarehouseTableCreateSerializer
        return DataWarehouseTableSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]  # ← Fixed
        else:
            permission_classes = [IsAuthenticated, CanViewDataSources]  # ← Fixed
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Rafraîchit la table"""
        table = self.get_object()
        service = DataWarehouseService()
        result = service.refresh_table(table)
        
        if result['success']:
            return success_response(result, "Table rafraîchie avec succès")
        else:
            return error_response(
                f"Erreur de rafraîchissement: {result.get('error')}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analyse la table (statistiques)"""
        table = self.get_object()
        service = DataWarehouseService()
        result = service.analyze_table(table)
        
        if result['success']:
            return success_response(result, "Table analysée avec succès")
        else:
            return error_response(
                f"Erreur d'analyse: {result.get('error')}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """Optimise la table (VACUUM)"""
        table = self.get_object()
        service = DataWarehouseService()
        result = service.optimize_table(table)
        
        if result['success']:
            return success_response(result, "Table optimisée avec succès")
        else:
            return error_response(
                f"Erreur d'optimisation: {result.get('error')}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Métriques de la table"""
        table = self.get_object()
        metrics = table.metrics.all()
        
        hours = int(request.query_params.get('hours', 24))
        if hours:
            cutoff = timezone.now() - timedelta(hours=hours)
            metrics = metrics.filter(timestamp__gte=cutoff)
        
        limit = int(request.query_params.get('limit', 100))
        metrics = metrics[:limit]
        
        serializer = DataWarehouseMetricSerializer(metrics, many=True)
        return success_response(serializer.data, "Métriques récupérées")
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Logs de la table"""
        table = self.get_object()
        logs = table.logs.all()
        
        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level)
        
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]
        
        serializer = DataWarehouseLogSerializer(logs, many=True)
        return success_response(serializer.data, "Logs récupérés")


class FactTableViewSet(DataWarehouseTableViewSet):
    """ViewSet pour FactTable"""
    
    queryset = FactTable.objects.all().select_related('schema', 'source_table', 'source_pipeline')
    serializer_class = FactTableSerializer
    filterset_class = FactTableFilter
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return DataWarehouseTableCreateSerializer
        return FactTableSerializer
    
    @action(detail=True, methods=['get'])
    def measures(self, request, pk=None):
        """Liste les mesures de la table des faits"""
        fact_table = self.get_object()
        measures = fact_table.measures.filter(is_active=True)
        
        serializer = MeasureSerializer(measures, many=True)
        return success_response(serializer.data, "Mesures récupérées")
    
    @action(detail=True, methods=['post'])
    def add_measure(self, request, pk=None):
        """Ajoute une mesure"""
        fact_table = self.get_object()
        
        serializer = MeasureCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        measure = serializer.save(fact_table=fact_table)
        
        return created_response(
            MeasureSerializer(measure).data,
            "Mesure ajoutée avec succès"
        )


class DimensionTableViewSet(DataWarehouseTableViewSet):
    """ViewSet pour DimensionTable"""
    
    queryset = DimensionTable.objects.all().select_related('schema', 'source_table', 'source_pipeline')
    serializer_class = DimensionTableSerializer
    filterset_class = DimensionTableFilter
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return DataWarehouseTableCreateSerializer
        return DimensionTableSerializer
    
    @action(detail=True, methods=['get'])
    def attributes(self, request, pk=None):
        """Liste les attributs de la dimension"""
        dimension = self.get_object()
        attributes = dimension.attributes.filter(is_active=True)
        
        serializer = DimensionAttributeSerializer(attributes, many=True)
        return success_response(serializer.data, "Attributs récupérés")
    
    @action(detail=True, methods=['post'])
    def add_attribute(self, request, pk=None):
        """Ajoute un attribut"""
        dimension = self.get_object()
        
        serializer = DimensionAttributeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attribute = serializer.save(dimension_table=dimension)
        
        return created_response(
            DimensionAttributeSerializer(attribute).data,
            "Attribut ajouté avec succès"
        )


class StarSchemaViewSet(viewsets.ModelViewSet):
    """ViewSet pour StarSchema"""
    
    queryset = StarSchema.objects.all().select_related('fact_table', 'owner')
    serializer_class = StarSchemaSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StarSchemaFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'query_count', 'avg_query_time_ms', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StarSchemaCreateSerializer
        return StarSchemaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(
            StarSchemaSerializer(serializer.instance, context=self.get_serializer_context()).data,
            "Schéma en étoile créé avec succès"
        )

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]  # ← Fixed
        else:
            permission_classes = [IsAuthenticated, CanViewDataSources]  # ← Fixed
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute le schéma en étoile"""
        star_schema = self.get_object()
        
        limit = request.data.get('limit')
        params = request.data.get('params')
        
        service = StarSchemaService(star_schema)
        result = service.execute(limit, params)
        
        if result['success']:
            return success_response(result, "Schéma exécuté avec succès")
        else:
            return error_response(
                f"Erreur d'exécution: {result.get('error')}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def sql(self, request, pk=None):
        """Génère la requête SQL"""
        star_schema = self.get_object()
        sql = star_schema.generate_query()
        
        return success_response({'sql': sql}, "SQL généré avec succès")


class MeasureViewSet(viewsets.ModelViewSet):
    """ViewSet pour Measure"""
    
    queryset = Measure.objects.all().select_related('fact_table')
    serializer_class = MeasureSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MeasureFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['fact_table', 'name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MeasureCreateSerializer
        return MeasureSerializer


class DimensionAttributeViewSet(viewsets.ModelViewSet):
    """ViewSet pour DimensionAttribute"""
    
    queryset = DimensionAttribute.objects.all().select_related('dimension_table', 'parent_attribute')
    serializer_class = DimensionAttributeSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DimensionAttributeFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['dimension_table', 'name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DimensionAttributeCreateSerializer
        return DimensionAttributeSerializer


class AggregationTableViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour AggregationTable (lecture seule)"""
    
    queryset = AggregationTable.objects.all().select_related('base_table')
    serializer_class = AggregationTableSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AggregationTableFilter
    search_fields = ['name']
    ordering_fields = ['name', 'row_count', 'size_bytes', 'created_at']
    ordering = ['base_table', 'granularity']


class DataWarehouseLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour DataWarehouseLog (lecture seule)"""
    
    queryset = DataWarehouseLog.objects.all().select_related('table')
    serializer_class = DataWarehouseLogSerializer
    permission_classes = [IsAuthenticated]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'duration_ms']
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
            'by_operation': dict(recent.values_list('operation').annotate(count=Count('id'))),
        }
        
        return success_response(stats, "Statistiques des logs")


class DataWarehouseMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour DataWarehouseMetric (lecture seule)"""
    
    queryset = DataWarehouseMetric.objects.all().select_related('table')
    serializer_class = DataWarehouseMetricSerializer
    permission_classes = [IsAuthenticated]  # ← Fixed
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Dernières métriques pour chaque table"""
        table_id = request.query_params.get('table')
        
        if table_id:
            metrics = DataWarehouseMetric.objects.filter(
                table_id=table_id
            ).order_by('-timestamp')[:1]
            serializer = self.get_serializer(metrics, many=True)
            return success_response(serializer.data, "Dernière métrique")
        
        from django.db.models import Max
        
        latest_ids = DataWarehouseMetric.objects.values('table').annotate(
            latest=Max('id')
        ).values_list('latest', flat=True)
        
        latest_metrics = DataWarehouseMetric.objects.filter(id__in=latest_ids)
        
        page = self.paginate_queryset(latest_metrics)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(latest_metrics, many=True)
        return success_response(serializer.data, "Dernières métriques")
