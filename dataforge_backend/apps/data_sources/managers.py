# apps/data_sources/managers.py
"""
Gestionnaires personnalisés pour les modèles data_sources - Version optimisée
"""
from django.db import models
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta


class DataSourceManager(models.Manager):
    """Gestionnaire personnalisé pour DataSource"""
    
    def active(self):
        """Sources de données actives"""
        return self.filter(status='active')
    
    def by_type(self, source_type):
        """Sources par type"""
        return self.filter(source_type=source_type)
    
    def by_database_type(self, db_type):
        """Sources par type de base de données"""
        return self.filter(database_type=db_type)
    
    def by_owner(self, user):
        """Sources appartenant à un utilisateur"""
        return self.filter(owner=user)
    
    def by_team(self, team):
        """Sources appartenant à une équipe"""
        return self.filter(team=team)
    
    def needs_sync(self):
        """Sources nécessitant une synchronisation"""
        need_sync = []
        for source in self.all():
            if source.sync_frequency == 'manual' or not source.auto_refresh_enabled:
                continue
            
            if not source.last_sync:
                need_sync.append(source.id)
                continue
            
            delta = timezone.now() - source.last_sync
            
            intervals = {
                'realtime': timedelta(seconds=10),
                'every_5m': timedelta(minutes=5),
                'every_15m': timedelta(minutes=15),
                'every_30m': timedelta(minutes=30),
                'hourly': timedelta(hours=1),
                'every_6h': timedelta(hours=6),
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30),
            }
            
            if source.sync_frequency in intervals:
                if delta >= intervals[source.sync_frequency]:
                    need_sync.append(source.id)
        
        return self.filter(id__in=need_sync)
    
    def with_errors(self):
        """Sources avec erreurs"""
        return self.filter(status='error')
    
    def popular(self):
        """Sources les plus utilisées"""
        return self.annotate(
            query_count=Count('queries')
        ).order_by('-query_count')
    
    def unhealthy(self):
        """Sources en mauvaise santé"""
        return self.filter(
            Q(consecutive_failures__gte=3) |
            Q(error_count__gt=10) |
            Q(status='error')
        )
    
    def by_health(self, health_status):
        """Sources par état de santé"""
        if health_status == 'critical':
            return self.filter(consecutive_failures__gte=5)
        elif health_status == 'warning':
            return self.filter(consecutive_failures__gte=3, consecutive_failures__lt=5)
        elif health_status == 'fair':
            return self.filter(data_quality_score__gte=50, data_quality_score__lt=75)
        elif health_status == 'good':
            return self.filter(data_quality_score__gte=75)
        return self.all()
    
    def stats(self):
        """Statistiques globales"""
        total = self.count()
        active = self.filter(status='active').count()
        error = self.filter(status='error').count()
        
        by_type = dict(
            self.values_list('source_type').annotate(count=Count('id'))
        )
        
        by_database = dict(
            self.exclude(database_type__isnull=True)
            .values_list('database_type')
            .annotate(count=Count('id'))
        )
        
        total_queries = self.aggregate(Sum('total_queries'))['total_queries__sum'] or 0
        avg_success_rate = self.aggregate(Avg('success_rate'))['success_rate__avg'] or 0
        avg_quality_score = self.aggregate(Avg('data_quality_score'))['data_quality_score__avg'] or 0
        
        return {
            'total': total,
            'active': active,
            'error': error,
            'by_type': by_type,
            'by_database': by_database,
            'total_queries': total_queries,
            'avg_success_rate': round(avg_success_rate, 1),
            'avg_quality_score': round(avg_quality_score, 1),
        }


class DataTableManager(models.Manager):
    """Gestionnaire personnalisé pour DataTable"""
    
    def for_source(self, source):
        """Tables d'une source spécifique"""
        return self.filter(data_source=source)
    
    def with_schema(self):
        """Tables avec schéma défini"""
        return self.exclude(columns=[])
    
    def partitioned(self):
        """Tables partitionnées"""
        return self.filter(is_partitioned=True)
    
    def recently_updated(self, days=7):
        """Tables mises à jour récemment"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(last_updated__gte=cutoff)
    
    def by_size(self):
        """Tables classées par taille"""
        return self.filter(size_bytes__gt=0).order_by('-size_bytes')
    
    def stats(self):
        """Statistiques des tables"""
        return {
            'total': self.count(),
            'with_schema': self.with_schema().count(),
            'partitioned': self.partitioned().count(),
            'avg_rows': self.aggregate(Avg('row_count'))['row_count__avg'] or 0,
            'total_size_bytes': self.aggregate(Sum('size_bytes'))['size_bytes__sum'] or 0,
        }


class DataQueryManager(models.Manager):
    """Gestionnaire personnalisé pour DataQuery"""
    
    def favorites(self):
        """Requêtes favorites"""
        return self.filter(is_favorite=True)
    
    def public(self):
        """Requêtes publiques"""
        return self.filter(is_public=True)
    
    def by_user(self, user):
        """Requêtes d'un utilisateur"""
        return self.filter(created_by=user)
    
    def by_source(self, source):
        """Requêtes d'une source"""
        return self.filter(data_source=source)
    
    def popular(self):
        """Requêtes les plus exécutées"""
        return self.order_by('-execution_count')
    
    def cached(self):
        """Requêtes avec cache valide"""
        return self.exclude(cached_at__isnull=True).filter(
            cached_at__gte=timezone.now() - timedelta(seconds=models.F('cache_ttl'))
        )
    
    def slow(self, threshold_ms=5000):
        """Requêtes lentes"""
        return self.filter(avg_execution_time_ms__gte=threshold_ms)
    
    def stats(self):
        """Statistiques des requêtes"""
        return {
            'total': self.count(),
            'favorites': self.favorites().count(),
            'public': self.public().count(),
            'total_executions': self.aggregate(Sum('execution_count'))['execution_count__sum'] or 0,
            'avg_execution_time': self.aggregate(Avg('avg_execution_time_ms'))['avg_execution_time_ms__avg'] or 0,
        }


class DataSourceLogManager(models.Manager):
    """Gestionnaire personnalisé pour DataSourceLog"""
    
    def errors(self):
        """Logs d'erreur"""
        return self.filter(level='error')
    
    def warnings(self):
        """Logs d'avertissement"""
        return self.filter(level='warning')
    
    def since(self, minutes=60):
        """Logs depuis X minutes"""
        cutoff = timezone.now() - timedelta(minutes=minutes)
        return self.filter(created_at__gte=cutoff)
    
    def for_source(self, source):
        """Logs d'une source"""
        return self.filter(data_source=source)
    
    def by_level(self):
        """Statistiques par niveau"""
        return self.values('level').annotate(count=Count('id')).order_by('-count')
    
    def latest_errors(self, limit=10):
        """Dernières erreurs"""
        return self.errors().order_by('-created_at')[:limit]


class DataSourceMetricManager(models.Manager):
    """Gestionnaire personnalisé pour DataSourceMetric"""
    
    def latest_for_source(self, source):
        """Dernière métrique pour une source"""
        return self.filter(data_source=source).order_by('-timestamp').first()
    
    def average_for_period(self, source, hours=24):
        """Moyenne des métriques sur une période"""
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.filter(data_source=source, timestamp__gte=cutoff).aggregate(
            avg_query_time=Avg('query_time_ms'),
            avg_rows=Avg('rows_returned'),
            avg_cpu=Avg('cpu_time_ms'),
            avg_io=Avg('io_wait_ms'),
            max_query_time=models.Max('query_time_ms'),
            min_query_time=models.Min('query_time_ms'),
        )
    
    def timeline(self, source, hours=24):
        """Timeline des métriques"""
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.filter(data_source=source, timestamp__gte=cutoff).order_by('timestamp')


class StarSchemaManager(models.Manager):
    """Gestionnaire personnalisé pour StarSchema"""
    
    def active(self):
        """Schémas actifs"""
        return self.filter(is_active=True)
    
    def public(self):
        """Schémas publics"""
        return self.filter(is_public=True)
    
    def by_owner(self, user):
        """Schémas d'un propriétaire"""
        return self.filter(owner=user)
    
    def by_team(self, team):
        """Schémas d'une équipe"""
        return self.filter(team=team)
    
    def by_fact_table(self, fact_table):
        """Schémas utilisant une table des faits spécifique"""
        return self.filter(fact_table=fact_table)
    
    def by_dimension_table(self, dimension_table):
        """Schémas utilisant une table de dimension spécifique"""
        return self.filter(dimension_tables=dimension_table)
    
    def popular(self):
        """Schémas les plus utilisés"""
        return self.order_by('-query_count')
    
    def with_measures(self):
        """Schémas avec des mesures définies"""
        return self.exclude(measures=[])
    
    def with_dimensions(self):
        """Schémas avec des dimensions définies"""
        return self.exclude(dimension_columns={})
    
    def recently_queried(self, days=7):
        """Schémas interrogés récemment"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(last_queried_at__gte=cutoff)
    
    def stats(self):
        """Statistiques des schémas en étoile"""
        return {
            'total': self.count(),
            'active': self.active().count(),
            'public': self.public().count(),
            'with_measures': self.with_measures().count(),
            'with_dimensions': self.with_dimensions().count(),
            'total_queries': self.aggregate(Sum('query_count'))['query_count__sum'] or 0,
            'avg_queries': self.aggregate(Avg('query_count'))['query_count__avg'] or 0,
        }


class DataSourceFileManager(models.Manager):
    """Gestionnaire personnalisé pour DataSourceFile"""
    
    def pending(self):
        """Fichiers en attente de traitement"""
        return self.filter(process_status='pending')
    
    def processing(self):
        """Fichiers en cours de traitement"""
        return self.filter(process_status='processing')
    
    def completed(self):
        """Fichiers traités avec succès"""
        return self.filter(process_status='completed')
    
    def failed(self):
        """Fichiers ayant échoué"""
        return self.filter(process_status='failed')
    
    def by_source(self, source):
        """Fichiers d'une source"""
        return self.filter(data_source=source)
    
    def latest_version(self, source):
        """Dernière version du fichier pour une source"""
        return self.filter(data_source=source, is_latest=True).first()
    
    def stats(self):
        """Statistiques des fichiers"""
        return {
            'total': self.count(),
            'pending': self.pending().count(),
            'processing': self.processing().count(),
            'completed': self.completed().count(),
            'failed': self.failed().count(),
            'total_size_bytes': self.aggregate(Sum('file_size'))['file_size__sum'] or 0,
        }


class PowerQueryManager(models.Manager):
    """Gestionnaire personnalisé pour PowerQuery"""
    
    def enabled(self):
        """Power Queries activés"""
        return self.filter(is_enabled=True)
    
    def cached(self):
        """Power Queries avec cache activé"""
        return self.filter(is_cached=True)
    
    def by_source(self, source):
        """Power Queries d'une source"""
        return self.filter(data_source=source)
    
    def by_user(self, user):
        """Power Queries créés par un utilisateur"""
        return self.filter(created_by=user)
    
    def popular(self):
        """Power Queries les plus exécutés"""
        return self.order_by('-execution_count')
    
    def stats(self):
        """Statistiques des Power Queries"""
        return {
            'total': self.count(),
            'enabled': self.enabled().count(),
            'cached': self.cached().count(),
            'total_executions': self.aggregate(Sum('execution_count'))['execution_count__sum'] or 0,
            'avg_execution_time': self.aggregate(Avg('execution_time_ms'))['execution_time_ms__avg'] or 0,
        }