# apps/star_schema/views.py
"""
Vues pour l'application star_schema
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from apps.core.permissions import CanManageDataSources, CanViewDataSources
from apps.core.responses import success_response, error_response, created_response
from apps.core.pagination import StandardPagination

from .models import (
    DimensionalSchema,  # ← Changé de StarSchema à DimensionalSchema
    FactRelationship, 
    DimensionHierarchy,
    CustomCalculation, 
    GalaxySchema
)
from .serializers import (
    DimensionalSchemaSerializer, DimensionalSchemaDetailSerializer,
    DimensionalSchemaCreateSerializer, DimensionalSchemaUpdateSerializer,
    DimensionalSchemaExecuteSerializer,
    FactRelationshipSerializer, DimensionHierarchySerializer,
    CustomCalculationSerializer, GalaxySchemaSerializer, GalaxySchemaDetailSerializer
)
from .filters import (
    DimensionalSchemaFilter, FactRelationshipFilter, 
    DimensionHierarchyFilter, CustomCalculationFilter, GalaxySchemaFilter
)
from .services import DimensionalSchemaService, GalaxySchemaService


class DimensionalSchemaViewSet(viewsets.ModelViewSet):
    """ViewSet pour DimensionalSchema"""
    
    queryset = DimensionalSchema.objects.all().select_related('owner', 'team', 'created_by')
    serializer_class = DimensionalSchemaSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DimensionalSchemaFilter
    search_fields = ['name', 'description', 'category', 'business_domain']
    ordering_fields = ['name', 'created_at', 'query_count', 'avg_query_time_ms']
    ordering = ['-query_count', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DimensionalSchemaDetailSerializer
        elif self.action == 'create':
            return DimensionalSchemaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DimensionalSchemaUpdateSerializer
        return DimensionalSchemaSerializer
    
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
        """Exécute le schéma dimensionnel"""
        schema = self.get_object()
        
        serializer = DimensionalSchemaExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = DimensionalSchemaService(schema)
        result = service.execute(
            filters=serializer.validated_data.get('filters'),
            limit=serializer.validated_data.get('limit'),
            offset=serializer.validated_data.get('offset')
        )
        
        if result['success']:
            format_type = serializer.validated_data.get('format', 'json')
            
            if format_type == 'csv':
                csv_data = service.export('csv', serializer.validated_data.get('filters'))
                response = HttpResponse(csv_data, content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="{schema.name}.csv"'
                return response
            
            elif format_type == 'excel':
                excel_data = service.export('excel', serializer.validated_data.get('filters'))
                response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{schema.name}.xlsx"'
                return response
            
            return success_response(
                {
                    'data': result.get('data'),
                    'columns': result.get('columns'),
                    'row_count': result.get('row_count'),
                    'execution_time_ms': result.get('execution_time_ms'),
                    'from_cache': result.get('from_cache', False)
                },
                "Schéma exécuté avec succès"
            )
        else:
            return error_response(
                f"Erreur d'exécution: {result.get('error')}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def sql(self, request, pk=None):
        """Génère la requête SQL"""
        schema = self.get_object()
        sql = schema.generate_query()
        
        return success_response({'sql': sql}, "SQL généré avec succès")
    
    @action(detail=True, methods=['get', 'post'])
    def validate(self, request, pk=None):
        """Valide la configuration du schéma. GET ou POST acceptés —
        l'UI appelle en POST car c'est une action explicite déclenchée
        par un bouton ; GET reste accepté pour les sondes/debug."""
        schema = self.get_object()
        service = DimensionalSchemaService(schema)
        result = service.validate()

        return success_response(result, "Validation terminée")
    
    @action(detail=True, methods=['post'])
    def clear_cache(self, request, pk=None):
        """Vide le cache du schéma"""
        schema = self.get_object()
        
        from django.core.cache import cache
        cache.delete_pattern(f"dimensional_schema_{schema.id}_*")
        
        return success_response(None, "Cache vidé avec succès")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques globales"""
        stats = DimensionalSchema.objects.stats()
        
        return success_response(stats, "Statistiques récupérées")


class FactRelationshipViewSet(viewsets.ModelViewSet):
    """ViewSet pour FactRelationship"""
    
    queryset = FactRelationship.objects.all().select_related('from_fact', 'to_fact')
    serializer_class = FactRelationshipSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FactRelationshipFilter
    search_fields = ['name']
    ordering_fields = ['name', 'cardinality']
    ordering = ['name']


class DimensionHierarchyViewSet(viewsets.ModelViewSet):
    """ViewSet pour DimensionHierarchy"""
    
    queryset = DimensionHierarchy.objects.all().select_related('dimension_table')
    serializer_class = DimensionHierarchySerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DimensionHierarchyFilter
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class CustomCalculationViewSet(viewsets.ModelViewSet):
    """ViewSet pour CustomCalculation"""
    
    queryset = CustomCalculation.objects.all().select_related('dimensional_schema')
    serializer_class = CustomCalculationSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CustomCalculationFilter
    search_fields = ['name']
    ordering_fields = ['name', 'calculation_type']
    ordering = ['name']


class GalaxySchemaViewSet(viewsets.ModelViewSet):
    """ViewSet pour GalaxySchema"""
    
    queryset = GalaxySchema.objects.all().select_related('owner')
    serializer_class = GalaxySchemaSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = GalaxySchemaFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GalaxySchemaDetailSerializer
        return GalaxySchemaSerializer
    
    @action(detail=True, methods=['post'])
    def execute_unified(self, request, pk=None):
        """Exécute tous les schémas de la galaxie"""
        galaxy = self.get_object()
        service = GalaxySchemaService(galaxy)
        result = service.execute_unified(request.data.get('filters'))
        
        return success_response(result, "Galaxie exécutée avec succès")
    
    @action(detail=True, methods=['get'])
    def unified_sql(self, request, pk=None):
        """Génère la requête unifiée"""
        galaxy = self.get_object()
        sql = galaxy.generate_unified_query()
        
        return success_response({'sql': sql}, "SQL unifié généré")
