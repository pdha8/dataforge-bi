# apps/visualizations/views.py
"""
Vues pour l'application visualizations
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q

from apps.core.permissions import CanManageDataSources, CanViewDataSources
from apps.core.responses import success_response, error_response, created_response
from apps.core.pagination import StandardPagination

from .models import (
    Dashboard, Widget, KPI, Report, Favorite, VisualizationActivity
)
from .serializers import (
    DashboardSerializer, DashboardDetailSerializer, DashboardCreateSerializer,
    DashboardUpdateSerializer, WidgetSerializer, KPISerializer,
    ReportSerializer, FavoriteSerializer, VisualizationActivitySerializer
)
from .filters import (
    DashboardFilter, WidgetFilter, KPIFilter, ReportFilter, ActivityFilter
)
from .services import (
    DashboardService, WidgetDataService, WidgetRenderService,
    KPIService, ReportGenerationService
)


class DashboardViewSet(viewsets.ModelViewSet):
    """ViewSet pour Dashboard"""
    
    queryset = Dashboard.objects.all().select_related('owner', 'team', 'published_by')
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated, CanViewDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DashboardFilter
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'view_count', 'created_at', 'last_viewed']
    ordering = ['-view_count', 'name']
    
    def get_queryset(self):
        user = self.request.user
        return Dashboard.objects.accessible_by(user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DashboardDetailSerializer
        elif self.action == 'create':
            return DashboardCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DashboardUpdateSerializer
        return DashboardSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanManageDataSources]
        else:
            permission_classes = [IsAuthenticated, CanViewDataSources]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        return instance
    
    @action(detail=True, methods=['get'])
    def render(self, request, pk=None):
        """Rend le tableau de bord complet"""
        dashboard = self.get_object()
        service = DashboardService(dashboard)
        result = service.render()
        
        # Enregistrer l'activité
        VisualizationActivity.objects.create(
            user=request.user,
            dashboard=dashboard,
            activity_type='view',
            description=f"Visualisation du tableau de bord '{dashboard.name}'",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        dashboard.increment_view()
        
        return success_response(result, "Tableau de bord rendu avec succès")
    
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Exporte le tableau de bord"""
        dashboard = self.get_object()
        format_type = request.data.get('format', dashboard.default_export_format)
        
        from .services import DashboardExportService
        service = DashboardExportService(dashboard)
        result = service.export(format_type, request.data.get('filters'))
        
        if result['success']:
            # Enregistrer l'activité
            VisualizationActivity.objects.create(
                user=request.user,
                dashboard=dashboard,
                activity_type='export',
                description=f"Export du tableau de bord '{dashboard.name}' en {format_type}",
                metadata={'format': format_type},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return success_response(result, "Tableau de bord exporté avec succès")
        else:
            return error_response(result.get('error', 'Erreur d\'export'), status_code=500)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplique le tableau de bord"""
        dashboard = self.get_object()
        new_dashboard = dashboard.duplicate(request.user)
        
        return created_response(
            DashboardSerializer(new_dashboard).data,
            "Tableau de bord dupliqué avec succès"
        )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publie le tableau de bord"""
        dashboard = self.get_object()
        dashboard.status = 'published'
        dashboard.published_at = timezone.now()
        dashboard.published_by = request.user
        dashboard.save()
        
        return success_response(None, "Tableau de bord publié avec succès")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des tableaux de bord"""
        stats = Dashboard.objects.stats()
        return success_response(stats, "Statistiques récupérées")


class WidgetViewSet(viewsets.ModelViewSet):
    """ViewSet pour Widget"""
    
    queryset = Widget.objects.all().select_related('dashboard', 'dimensional_schema')
    serializer_class = WidgetSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WidgetFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'render_count']
    ordering = ['dashboard', 'order']
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Récupère les données du widget"""
        widget = self.get_object()
        service = WidgetDataService(widget)
        data = service.fetch_data(request.query_params.dict())
        
        return success_response(data, "Données récupérées")
    
    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """Rend le widget"""
        widget = self.get_object()
        service = WidgetRenderService(widget)
        result = service.render(request.data.get('data'))
        
        return success_response(result, "Widget rendu avec succès")
    
    @action(detail=True, methods=['post'])
    def clear_cache(self, request, pk=None):
        """Vide le cache du widget"""
        widget = self.get_object()
        widget.cached_data = {}
        widget.cached_at = None
        widget.save()
        
        return success_response(None, "Cache vidé avec succès")


class KPIViewSet(viewsets.ModelViewSet):
    """ViewSet pour KPI"""
    
    queryset = KPI.objects.all().select_related('dimensional_schema', 'measure', 'dashboard')
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = KPIFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'current_value']
    ordering = ['order', 'name']
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calcule la valeur du KPI"""
        kpi = self.get_object()
        service = KPIService(kpi)
        result = service.calculate(request.data.get('filters'))
        
        return success_response(result, "KPI calculé avec succès")
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Liste des KPIs critiques"""
        kpis = KPI.objects.critical()
        page = self.paginate_queryset(kpis)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def warning(self, request):
        """Liste des KPIs en avertissement"""
        kpis = KPI.objects.warning()
        page = self.paginate_queryset(kpis)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des KPIs"""
        stats = KPI.objects.stats()
        return success_response(stats, "Statistiques récupérées")


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet pour Report"""
    
    queryset = Report.objects.all().select_related('dashboard', 'owner')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, CanManageDataSources]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReportFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_generated']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Génère le rapport"""
        report = self.get_object()
        service = ReportGenerationService(report)
        result = service.generate(request.user)
        
        if result['success']:
            return success_response(result, "Rapport généré avec succès")
        else:
            return error_response(result.get('error'), status_code=500)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Liste des rapports en attente"""
        reports = Report.objects.pending()
        page = self.paginate_queryset(reports)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des rapports"""
        stats = Report.objects.stats()
        return success_response(stats, "Statistiques récupérées")


class FavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet pour Favorite"""
    
    queryset = Favorite.objects.all().select_related('user', 'dashboard', 'kpi', 'report')
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['order', 'created_at']
    ordering = ['user', 'order']
    
    def get_queryset(self):
        return Favorite.objects.for_user(self.request.user)
    
    @action(detail=False, methods=['post'])
    def add(self, request):
        """Ajoute un favori"""
        item_id = request.data.get('item_id')
        item_type = request.data.get('item_type', 'dashboard')
        notes = request.data.get('notes', '')
        
        if item_type == 'dashboard':
            item = Dashboard.objects.get(id=item_id)
        elif item_type == 'kpi':
            item = KPI.objects.get(id=item_id)
        elif item_type == 'report':
            item = Report.objects.get(id=item_id)
        else:
            return error_response("Type d'élément invalide", status_code=400)
        
        favorite = Favorite.objects.add_favorite(request.user, item, item_type, notes)
        
        return created_response(
            FavoriteSerializer(favorite).data,
            "Favori ajouté avec succès"
        )
    
    @action(detail=False, methods=['post'])
    def remove(self, request):
        """Supprime un favori"""
        item_id = request.data.get('item_id')
        item_type = request.data.get('item_type', 'dashboard')
        
        if item_type == 'dashboard':
            item = Dashboard.objects.get(id=item_id)
        elif item_type == 'kpi':
            item = KPI.objects.get(id=item_id)
        elif item_type == 'report':
            item = Report.objects.get(id=item_id)
        else:
            return error_response("Type d'élément invalide", status_code=400)
        
        Favorite.objects.remove_favorite(request.user, item, item_type)
        
        return success_response(None, "Favori supprimé avec succès")


class VisualizationActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour VisualizationActivity (lecture seule)"""
    
    queryset = VisualizationActivity.objects.all().select_related('user', 'dashboard', 'widget')
    serializer_class = VisualizationActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ActivityFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return VisualizationActivity.objects.all()
        return VisualizationActivity.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des activités"""
        queryset = self.get_queryset()
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        
        stats = {
            'total': queryset.count(),
            'last_24h': queryset.filter(created_at__gte=last_24h).count(),
            'by_type': dict(
                queryset.values_list('activity_type').annotate(count=Count('id'))
            ),
            'by_user': dict(
                queryset.values_list('user__email').annotate(count=Count('id'))
            )[:10]
        }
        
        return success_response(stats, "Statistiques récupérées")
