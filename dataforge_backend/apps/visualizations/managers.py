# apps/visualizations/managers.py
"""
Gestionnaires personnalisés pour l'application visualizations
"""
from django.db import models
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta


class DashboardManager(models.Manager):
    """Gestionnaire personnalisé pour Dashboard"""
    
    def active(self):
        """Tableaux de bord actifs"""
        return self.filter(status='published')
    
    def by_type(self, dashboard_type):
        """Tableaux de bord par type"""
        return self.filter(dashboard_type=dashboard_type)
    
    def by_owner(self, user):
        """Tableaux de bord d'un propriétaire"""
        return self.filter(owner=user)
    
    def by_team(self, team):
        """Tableaux de bord d'une équipe"""
        return self.filter(team=team)
    
    def accessible_by(self, user):
        """Tableaux de bord accessibles à un utilisateur"""
        if user.is_superuser or user.is_admin:
            return self.all()
        
        return self.filter(
            Q(owner=user) |
            Q(team__in=user.teams.all()) |
            Q(allowed_users=user) |
            Q(access_level='public')
        ).distinct()
    
    def popular(self):
        """Tableaux de bord les plus populaires"""
        return self.order_by('-view_count')
    
    def recently_used(self, days=7):
        """Tableaux de bord récemment utilisés"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(last_viewed__gte=cutoff)
    
    def with_widgets(self):
        """Tableaux de bord avec au moins un widget"""
        return self.annotate(widget_count=Count('widgets')).filter(widget_count__gt=0)
    
    def search(self, query):
        """Recherche dans les tableaux de bord"""
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(tags__contains=[query])
        )
    
    def stats(self):
        """Statistiques des tableaux de bord"""
        total = self.count()
        published = self.filter(status='published').count()
        by_type = dict(
            self.values_list('dashboard_type').annotate(count=Count('id'))
        )
        total_views = self.aggregate(Sum('view_count'))['view_count__sum'] or 0
        avg_views = self.aggregate(Avg('view_count'))['view_count__avg'] or 0
        
        return {
            'total': total,
            'published': published,
            'by_type': by_type,
            'total_views': total_views,
            'avg_views': round(avg_views, 1),
        }


class WidgetManager(models.Manager):
    """Gestionnaire personnalisé pour Widget"""
    
    def enabled(self):
        """Widgets activés"""
        return self.filter(is_enabled=True)
    
    def by_type(self, widget_type):
        """Widgets par type"""
        return self.filter(widget_type=widget_type)
    
    def for_dashboard(self, dashboard):
        """Widgets d'un tableau de bord"""
        return self.filter(dashboard=dashboard, is_enabled=True)
    
    def cached(self):
        """Widgets avec cache activé"""
        return self.filter(cache_enabled=True)
    
    def popular(self):
        """Widgets les plus rendus"""
        return self.order_by('-render_count')
    
    def slow(self, threshold_ms=1000):
        """Widgets lents"""
        return self.filter(avg_render_time_ms__gte=threshold_ms)
    
    def needs_refresh(self):
        """Widgets nécessitant un rafraîchissement"""
        cutoff = timezone.now() - timedelta(seconds=300)
        return self.filter(cached_at__lt=cutoff, cache_enabled=True)


class KpiManager(models.Manager):
    """Gestionnaire personnalisé pour KPI"""
    
    def active(self):
        """KPIs actifs"""
        return self.filter(is_active=True)
    
    def by_type(self, kpi_type):
        """KPIs par type"""
        return self.filter(kpi_type=kpi_type)
    
    def by_schema(self, schema):
        """KPIs d'un schéma"""
        return self.filter(dimensional_schema=schema)
    
    def for_dashboard(self, dashboard):
        """KPIs d'un tableau de bord"""
        return self.filter(dashboard=dashboard)
    
    def with_trend(self):
        """KPIs avec suivi de tendance"""
        return self.filter(track_trend=True)
    
    def critical(self):
        """KPIs en état critique"""
        kpis = []
        for kpi in self.active():
            if kpi.get_status() == 'critical':
                kpis.append(kpi.id)
        return self.filter(id__in=kpis)
    
    def warning(self):
        """KPIs en état d'avertissement"""
        kpis = []
        for kpi in self.active():
            if kpi.get_status() == 'warning':
                kpis.append(kpi.id)
        return self.filter(id__in=kpis)
    
    def stats(self):
        """Statistiques des KPIs"""
        total = self.count()
        active = self.active().count()
        by_type = dict(
            self.values_list('kpi_type').annotate(count=Count('id'))
        )
        with_trend = self.with_trend().count()
        
        return {
            'total': total,
            'active': active,
            'by_type': by_type,
            'with_trend': with_trend,
        }


class ReportManager(models.Manager):
    """Gestionnaire personnalisé pour Report"""
    
    def active(self):
        """Rapports actifs"""
        return self.filter(is_active=True)
    
    def by_format(self, format_type):
        """Rapports par format"""
        return self.filter(format=format_type)
    
    def scheduled(self):
        """Rapports planifiés"""
        return self.filter(schedule__isnull=False, schedule__gt='')
    
    def pending(self):
        """Rapports en attente de génération"""
        pending = []
        for report in self.active().filter(schedule__isnull=False, schedule__gt=''):
            try:
                next_run = report.get_next_run()
                if next_run and next_run <= timezone.now():
                    pending.append(report.id)
            except Exception:
                pass
        return self.filter(id__in=pending)
    
    def recently_generated(self, days=7):
        """Rapports générés récemment"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(last_generated__gte=cutoff)
    
    def stats(self):
        """Statistiques des rapports"""
        total = self.count()
        active = self.active().count()
        scheduled = self.scheduled().count()
        by_format = dict(
            self.values_list('format').annotate(count=Count('id'))
        )
        total_generations = self.aggregate(Sum('generation_count'))['generation_count__sum'] or 0
        
        return {
            'total': total,
            'active': active,
            'scheduled': scheduled,
            'by_format': by_format,
            'total_generations': total_generations,
        }


class FavoriteManager(models.Manager):
    """Gestionnaire personnalisé pour Favorite"""
    
    def for_user(self, user):
        """Favoris d'un utilisateur"""
        return self.filter(user=user).order_by('order')
    
    def for_dashboard(self, dashboard):
        """Favoris pour un tableau de bord"""
        return self.filter(dashboard=dashboard)
    
    def add_favorite(self, user, item, item_type='dashboard', notes=''):
        """Ajoute un favori"""
        kwargs = {'user': user, 'notes': notes}
        
        if item_type == 'dashboard':
            kwargs['dashboard'] = item
        elif item_type == 'kpi':
            kwargs['kpi'] = item
        elif item_type == 'report':
            kwargs['report'] = item
        
        return self.get_or_create(**kwargs)[0]
    
    def remove_favorite(self, user, item, item_type='dashboard'):
        """Supprime un favori"""
        kwargs = {'user': user}
        
        if item_type == 'dashboard':
            kwargs['dashboard'] = item
        elif item_type == 'kpi':
            kwargs['kpi'] = item
        elif item_type == 'report':
            kwargs['report'] = item
        
        return self.filter(**kwargs).delete()