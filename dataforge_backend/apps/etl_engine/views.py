# apps/etl_engine/views.py
"""
Vues pour l'application etl_engine
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.db import models
from datetime import timedelta
import uuid

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
    ETLPipeline, Transformation, ExecutionLog,
    TargetSchema, SourceSchema, PipelineNotification
)
from .serializers import (
    ETLPipelineSerializer, ETLPipelineDetailSerializer,
    ETLPipelineCreateSerializer, ETLPipelineUpdateSerializer,
    TransformationSerializer, TransformationDetailSerializer,
    TransformationCreateSerializer,
    ExecutionLogSerializer, ExecutionLogDetailSerializer,
    ExecutionTriggerSerializer,
    TargetSchemaSerializer, SourceSchemaSerializer,
    PipelineNotificationSerializer,
    ETLPipelineStatsSerializer, ExecutionStatsSerializer
)
from .filters import (
    ETLPipelineFilter, TransformationFilter, ExecutionLogFilter
)
from .services import ETLPipelineService, ETLOrchestrator


class ETLPipelineViewSet(viewsets.ModelViewSet):
    """ViewSet pour ETLPipeline"""
    
    queryset = ETLPipeline.objects.all().select_related('source', 'target', 'owner', 'team', 'created_by')
    serializer_class = ETLPipelineSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ETLPipelineFilter
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'created_at', 'last_execution', 'priority', 'execution_count']
    ordering = ['-priority', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ETLPipelineDetailSerializer
        elif self.action == 'create':
            return ETLPipelineCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ETLPipelineUpdateSerializer
        return ETLPipelineSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]
        else:
            permission_classes = [IsAuthenticated, CanViewDataSources]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return created_response(serializer.data, "Pipeline ETL créé avec succès")

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        return instance

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécute le pipeline ETL"""
        pipeline = self.get_object()
        
        # Vérifier les permissions
        if pipeline.status != 'active':
            return error_response(
                f"Le pipeline doit être actif (statut actuel: {pipeline.status})",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ExecutionTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        orchestrator = ETLOrchestrator()
        result = orchestrator.execute_pipeline(
            pipeline.id,
            params=serializer.validated_data.get('params'),
            triggered_by='api',
            user=request.user
        )
        
        if result['success']:
            return success_response(
                {
                    'execution_id': result.get('execution_id'),
                    'rows_read': result.get('rows_read', 0),
                    'rows_written': result.get('rows_written', 0),
                    'duration_seconds': result.get('duration_seconds')
                },
                "Pipeline exécuté avec succès"
            )
        else:
            return error_response(
                f"Erreur d'exécution: {result.get('error')}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Liste les exécutions du pipeline"""
        pipeline = self.get_object()
        executions = pipeline.executions.all()
        
        # Filtres
        status_filter = request.query_params.get('status')
        if status_filter:
            executions = executions.filter(status=status_filter)
        
        limit = int(request.query_params.get('limit', 50))
        executions = executions[:limit]
        
        serializer = ExecutionLogSerializer(executions, many=True)
        return success_response(serializer.data, "Exécutions récupérées")
    
    @action(detail=True, methods=['get'])
    def transformations(self, request, pk=None):
        """Liste les transformations du pipeline"""
        pipeline = self.get_object()
        transformations = pipeline.transformation_list.all()
        
        serializer = TransformationSerializer(transformations, many=True)
        return success_response(serializer.data, "Transformations récupérées")
    
    @action(detail=True, methods=['get'])
    def target_schema(self, request, pk=None):
        """Récupère le schéma cible"""
        pipeline = self.get_object()
        if hasattr(pipeline, 'target_schema'):
            serializer = TargetSchemaSerializer(pipeline.target_schema)
            return success_response(serializer.data, "Schéma cible récupéré")
        return success_response(None, "Aucun schéma cible configuré")
    
    @action(detail=True, methods=['get'])
    def source_schema(self, request, pk=None):
        """Récupère le schéma source"""
        pipeline = self.get_object()
        if hasattr(pipeline, 'source_schema'):
            serializer = SourceSchemaSerializer(pipeline.source_schema)
            return success_response(serializer.data, "Schéma source récupéré")
        return success_response(None, "Aucun schéma source configuré")
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Active/désactive le pipeline"""
        pipeline = self.get_object()
        
        new_status = request.data.get('status')
        if new_status not in ['active', 'paused', 'archived']:
            return error_response(
                "Statut invalide. Choisir parmi: active, paused, archived",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = pipeline.status
        pipeline.status = new_status
        pipeline.save()
        
        return success_response(
            {'status': pipeline.status},
            f"Statut du pipeline changé de {old_status} à {new_status}"
        )
    
    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """Liste les dépendances du pipeline"""
        pipeline = self.get_object()
        deps = pipeline.dependencies.all()
        serializer = ETLPipelineSerializer(deps, many=True)
        return success_response(serializer.data, "Dépendances récupérées")

    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """Ajoute une dépendance au pipeline"""
        pipeline = self.get_object()
        dep_id = request.data.get('dependency_id')
        if not dep_id:
            return error_response("dependency_id requis", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            dep = ETLPipeline.objects.get(pk=dep_id)
        except ETLPipeline.DoesNotExist:
            return not_found_response("Pipeline dépendance non trouvé")
        if dep.id == pipeline.id:
            return error_response("Un pipeline ne peut pas dépendre de lui-même", status_code=status.HTTP_400_BAD_REQUEST)
        pipeline.dependencies.add(dep)
        return success_response(None, "Dépendance ajoutée")

    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, pk=None):
        """Supprime une dépendance du pipeline"""
        pipeline = self.get_object()
        dep_id = request.data.get('dependency_id')
        if not dep_id:
            return error_response("dependency_id requis", status_code=status.HTTP_400_BAD_REQUEST)
        try:
            dep = ETLPipeline.objects.get(pk=dep_id)
        except ETLPipeline.DoesNotExist:
            return not_found_response("Pipeline dépendance non trouvé")
        pipeline.dependencies.remove(dep)
        return success_response(None, "Dépendance supprimée")

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques globales des pipelines"""
        if not request.user.is_admin:
            return forbidden_response("Accès administrateur requis")
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        active = queryset.filter(status='active').count()
        error = queryset.filter(status='error').count()
        
        by_type = dict(
            queryset.values_list('pipeline_type').annotate(count=Count('id'))
        )
        
        agg = queryset.aggregate(
            total_executions=Sum('execution_count'),
            total_success=Sum('success_count'),
            avg_duration=Avg('avg_duration_seconds'),
        )
        total_executions = agg['total_executions'] or 0
        avg_duration = agg['avg_duration'] or 0
        total_success = agg['total_success'] or 0
        avg_success_rate = (total_success / total_executions * 100) if total_executions > 0 else 100.0
        
        stats_data = {
            'total': total,
            'active': active,
            'error': error,
            'by_type': by_type,
            'total_executions': total_executions,
            'avg_duration_seconds': round(avg_duration, 2),
            'avg_success_rate': round(avg_success_rate, 1),
        }
        
        return success_response(stats_data, "Statistiques récupérées")
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """État de santé des pipelines"""
        queryset = self.get_queryset()
        
        critical = 0
        warning = 0
        poor = 0
        fair = 0
        good = 0
        
        for pipeline in queryset:
            health = pipeline.health_status
            if health == 'critical':
                critical += 1
            elif health == 'warning':
                warning += 1
            elif health == 'poor':
                poor += 1
            elif health == 'fair':
                fair += 1
            else:
                good += 1
        
        health_data = {
            'critical': critical,
            'warning': warning,
            'poor': poor,
            'fair': fair,
            'good': good,
            'total': queryset.count()
        }
        
        return success_response(health_data, "État de santé récupéré")


class TransformationViewSet(viewsets.ModelViewSet):
    """ViewSet pour Transformation"""
    
    queryset = Transformation.objects.all().select_related('pipeline')
    serializer_class = TransformationSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransformationFilter
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'execution_count', 'avg_duration_ms']
    ordering = ['pipeline', 'order']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TransformationDetailSerializer
        elif self.action == 'create':
            return TransformationCreateSerializer
        return TransformationSerializer
    
    def perform_create(self, serializer):
        # Vérifier l'ordre
        pipeline = serializer.validated_data.get('pipeline')
        order = serializer.validated_data.get('order', 0)
        
        if order == 0:
            last_order = pipeline.transformation_list.aggregate(models.Max('order'))['order__max'] or 0
            serializer.save(order=last_order + 1)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def toggle_enabled(self, request, pk=None):
        """Active/désactive la transformation"""
        transformation = self.get_object()
        transformation.is_enabled = not transformation.is_enabled
        transformation.save()
        
        status_msg = "activée" if transformation.is_enabled else "désactivée"
        return success_response(
            {'is_enabled': transformation.is_enabled},
            f"Transformation {status_msg}"
        )
    
    @action(detail=True, methods=['post'])
    def move_up(self, request, pk=None):
        """Déplace la transformation vers le haut"""
        transformation = self.get_object()
        transformation.move_up()
        return success_response(None, "Transformation déplacée vers le haut")
    
    @action(detail=True, methods=['post'])
    def move_down(self, request, pk=None):
        """Déplace la transformation vers le bas"""
        transformation = self.get_object()
        transformation.move_down()
        return success_response(None, "Transformation déplacée vers le bas")


class ExecutionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour ExecutionLog (lecture seule)"""
    
    queryset = ExecutionLog.objects.all().select_related('pipeline', 'triggered_by_user')
    serializer_class = ExecutionLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExecutionLogFilter
    search_fields = ['execution_id', 'error_message']
    ordering_fields = ['started_at', 'duration_seconds', 'rows_read', 'rows_written']
    ordering = ['-started_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExecutionLogDetailSerializer
        return ExecutionLogSerializer
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Détails complets de l'exécution"""
        execution = self.get_object()
        serializer = ExecutionLogDetailSerializer(execution)
        return success_response(serializer.data, "Détails de l'exécution")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des exécutions"""
        days = int(request.query_params.get('days', 7))
        cutoff = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(started_at__gte=cutoff)
        
        total = queryset.count()
        completed = queryset.filter(status='completed').count()
        failed = queryset.filter(status='failed').count()
        
        success_rate = (completed / total * 100) if total > 0 else 0
        avg_duration = queryset.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
        by_status = dict(
            queryset.values_list('status').annotate(count=Count('id'))
        )
        
        # Timeline par jour
        from django.db.models.functions import TruncDate
        timeline = queryset.annotate(
            date=TruncDate('started_at')
        ).values('date').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed'))
        ).order_by('date')
        
        stats_data = {
            'period': f"Derniers {days} jours",
            'total': total,
            'completed': completed,
            'failed': failed,
            'success_rate': round(success_rate, 1),
            'avg_duration_seconds': round(avg_duration, 2),
            'by_status': by_status,
            'timeline': list(timeline)
        }
        
        return success_response(stats_data, "Statistiques des exécutions")


class TargetSchemaViewSet(viewsets.ModelViewSet):
    """ViewSet pour TargetSchema"""
    
    queryset = TargetSchema.objects.all().select_related('pipeline')
    serializer_class = TargetSchemaSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['table_name', 'schema_name']
    
    @action(detail=True, methods=['get'])
    def generate_ddl(self, request, pk=None):
        """Génère le DDL pour la table cible"""
        schema = self.get_object()
        
        ddl = f"CREATE TABLE {schema.table_name} (\n"
        
        for col in schema.columns:
            col_name = col.get('name')
            col_type = col.get('type', 'VARCHAR(255)')
            nullable = 'NULL' if col.get('nullable', True) else 'NOT NULL'
            ddl += f"    {col_name} {col_type} {nullable},\n"
        
        if schema.primary_key:
            ddl += f"    PRIMARY KEY ({', '.join(schema.primary_key)})\n"
        else:
            ddl = ddl.rstrip(',\n') + "\n"
        
        ddl += ");"
        
        return success_response({'ddl': ddl}, "DDL généré avec succès")


class SourceSchemaViewSet(viewsets.ModelViewSet):
    """ViewSet pour SourceSchema"""
    
    queryset = SourceSchema.objects.all().select_related('pipeline')
    serializer_class = SourceSchemaSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['table_name', 'query']
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Aperçu des données source"""
        schema = self.get_object()
        
        service = DataSourceService(schema.pipeline.source)
        
        if schema.query:
            query = schema.query
        elif schema.table_name:
            query = f"SELECT * FROM {schema.table_name} LIMIT 10"
        else:
            return error_response("Aucune source configurée", status_code=400)
        
        result = service.execute_query(query)
        
        if result['success']:
            return success_response(result, "Aperçu des données source")
        else:
            return error_response(
                f"Erreur: {result.get('error')}",
                status_code=500
            )


class PipelineNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour PipelineNotification"""
    
    queryset = PipelineNotification.objects.all().select_related('pipeline')
    serializer_class = PipelineNotificationSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['recipient']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Teste la notification"""
        notification = self.get_object()
        
        # Simuler l'envoi
        return success_response(
            {'sent': True, 'channel': notification.channel, 'recipient': notification.recipient},
            "Notification test envoyée"
        )
