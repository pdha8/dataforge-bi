# apps/data_warehouse/managers.py
"""
Gestionnaires personnalisés pour l'application data_warehouse
"""
from django.db import models
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta


class TableManager(models.Manager):
    """Gestionnaire pour DataWarehouseTable"""
    
    def active(self):
        """Tables actives"""
        return self.filter(status='active')
    
    def by_type(self, table_type):
        """Tables par type"""
        return self.filter(table_type=table_type)
    
    def by_schema(self, schema):
        """Tables d'un schéma"""
        return self.filter(schema=schema)
    
    def needs_refresh(self):
        """Tables nécessitant un rafraîchissement"""
        need_refresh = []
        for table in self.filter(status='active'):
            if table.refresh_frequency == 'manual':
                continue
            
            if not table.last_refresh:
                need_refresh.append(table.id)
                continue
            
            delta = timezone.now() - table.last_refresh
            intervals = {
                'realtime': timedelta(seconds=10),
                'hourly': timedelta(hours=1),
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30),
            }
            
            if table.refresh_frequency in intervals:
                if delta >= intervals[table.refresh_frequency]:
                    need_refresh.append(table.id)
        
        return self.filter(id__in=need_refresh)
    
    def stats(self):
        """Statistiques globales"""
        total = self.count()
        active = self.filter(status='active').count()
        fact = self.filter(table_type='fact').count()
        dimension = self.filter(table_type='dimension').count()
        aggregate = self.filter(table_type='aggregate').count()
        
        total_size = self.aggregate(Sum('size_bytes'))['size_bytes__sum'] or 0
        
        return {
            'total': total,
            'active': active,
            'fact': fact,
            'dimension': dimension,
            'aggregate': aggregate,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }


class FactTableManager(models.Manager):
    """Gestionnaire pour les tables des faits"""
    
    def get_queryset(self):
        return super().get_queryset().filter(table_type='fact')
    
    def with_measures(self):
        """Tables des faits avec mesures"""
        return self.filter(measures__isnull=False).distinct()
    
    def by_granularity(self, granularity):
        """Tables des faits par granularité"""
        return self.filter(granularity=granularity)
    
    def stats(self):
        """Statistiques des tables des faits"""
        return {
            'total': self.count(),
            'with_measures': self.with_measures().count(),
            'by_granularity': dict(
                self.values_list('granularity').annotate(count=Count('id'))
            ),
            'total_rows': self.aggregate(Sum('row_count'))['row_count__sum'] or 0,
        }


class DimensionTableManager(models.Manager):
    """Gestionnaire pour les tables de dimension"""
    
    def get_queryset(self):
        return super().get_queryset().filter(table_type='dimension')
    
    def with_attributes(self):
        """Dimensions avec attributs"""
        return self.filter(attributes__isnull=False).distinct()
    
    def by_dimension_type(self, dim_type):
        """Dimensions par type"""
        return self.filter(dimension_type=dim_type)
    
    def scd_type(self, scd_type):
        """Dimensions par type SCD"""
        return self.filter(scd_type=scd_type)
    
    def stats(self):
        """Statistiques des dimensions"""
        return {
            'total': self.count(),
            'with_attributes': self.with_attributes().count(),
            'by_type': dict(
                self.values_list('dimension_type').annotate(count=Count('id'))
            ),
            'by_scd': dict(
                self.values_list('scd_type').annotate(count=Count('id'))
            ),
        }


class AggregateTableManager(models.Manager):
    """Gestionnaire pour les tables d'agrégation"""
    
    def get_queryset(self):
        return super().get_queryset()
    
    def by_base_table(self, base_table):
        """Agrégations par table de base"""
        return self.filter(base_table=base_table)
    
    def by_granularity(self, granularity):
        """Agrégations par granularité"""
        return self.filter(granularity=granularity)
    
    def compression_ratio(self):
        """Taux de compression moyen"""
        return self.aggregate(Avg('compression_ratio'))['compression_ratio__avg'] or 1.0
    
    def stats(self):
        """Statistiques des agrégations"""
        return {
            'total': self.count(),
            'by_granularity': dict(
                self.values_list('granularity').annotate(count=Count('id'))
            ),
            'total_rows': self.aggregate(Sum('row_count'))['row_count__sum'] or 0,
            'total_size_mb': round(
                (self.aggregate(Sum('size_bytes'))['size_bytes__sum'] or 0) / (1024 * 1024), 2
            ),
            'avg_compression': self.compression_ratio(),
        }


class StarSchemaManager(models.Manager):
    """Gestionnaire pour StarSchema"""
    
    def active(self):
        """Schémas actifs"""
        return self.filter(is_active=True)
    
    def by_fact_table(self, fact_table):
        """Schémas par table des faits"""
        return self.filter(fact_table=fact_table)
    
    def by_owner(self, user):
        """Schémas d'un propriétaire"""
        return self.filter(owner=user)
    
    def popular(self):
        """Schémas les plus utilisés"""
        return self.order_by('-query_count')
    
    def stats(self):
        """Statistiques des schémas en étoile"""
        return {
            'total': self.count(),
            'active': self.active().count(),
            'total_queries': self.aggregate(Sum('query_count'))['query_count__sum'] or 0,
            'avg_query_time': self.aggregate(Avg('avg_query_time_ms'))['avg_query_time_ms__avg'] or 0,
        }


# ============================================================================
# MANAGERS SUPPLEMENTAIRES
# ============================================================================

class ColumnManager(models.Manager):
    """Gestionnaire pour les colonnes (méthodes utilitaires)"""
    
    def for_table(self, table):
        """Colonnes d'une table spécifique"""
        return self.filter(table=table)
    
    def numeric_columns(self):
        """Colonnes numériques"""
        return self.filter(data_type__in=['integer', 'bigint', 'decimal', 'float'])
    
    def text_columns(self):
        """Colonnes texte"""
        return self.filter(data_type__in=['varchar', 'text'])
    
    def date_columns(self):
        """Colonnes date"""
        return self.filter(data_type__in=['date', 'datetime', 'timestamp'])


class IndexManager(models.Manager):
    """Gestionnaire pour les index"""
    
    def for_table(self, table):
        """Index d'une table spécifique"""
        return self.filter(table=table)
    
    def unique_indexes(self):
        """Index uniques"""
        return self.filter(is_unique=True)
    
    def clustered_indexes(self):
        """Index clusterisés"""
        return self.filter(is_clustered=True)