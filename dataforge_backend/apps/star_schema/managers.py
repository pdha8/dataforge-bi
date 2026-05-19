# apps/star_schema/managers.py
"""
Gestionnaires personnalisés pour l'application star_schema
"""
from django.db import models
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta


class DimensionalSchemaManager(models.Manager):  # ← Renommé
    """Gestionnaire personnalisé pour DimensionalSchema"""
    
    def active(self):
        return self.filter(status='active')
    
    def by_type(self, schema_type):
        return self.filter(schema_type=schema_type)
    
    def by_owner(self, user):
        return self.filter(owner=user)
    
    def by_team(self, team):
        return self.filter(team=team)
    
    def popular(self):
        return self.order_by('-query_count')
    
    def with_measures(self):
        return self.exclude(measures__isnull=True)
    
    def with_dimensions(self):
        return self.exclude(dimension_mapping={})
    
    def recently_queried(self, days=7):
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(last_queried_at__gte=cutoff)
    
    def search(self, query):
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(business_domain__icontains=query)
        )
    
    def stats(self):
        total = self.count()
        active = self.active().count()
        by_type = dict(self.values_list('schema_type').annotate(count=Count('id')))
        total_queries = self.aggregate(Sum('query_count'))['query_count__sum'] or 0
        avg_query_time = self.aggregate(Avg('avg_query_time_ms'))['avg_query_time_ms__avg'] or 0
        
        return {
            'total': total,
            'active': active,
            'by_type': by_type,
            'total_queries': total_queries,
            'avg_query_time_ms': round(avg_query_time, 2),
        }


class FactRelationshipManager(models.Manager):
    """Gestionnaire personnalisé pour FactRelationship"""
    
    def active(self):
        return self.filter(is_enabled=True)
    
    def for_fact(self, fact_table):
        return self.filter(Q(from_fact=fact_table) | Q(to_fact=fact_table))
    
    def outgoing(self, fact_table):
        return self.filter(from_fact=fact_table, is_enabled=True)
    
    def incoming(self, fact_table):
        return self.filter(to_fact=fact_table, is_enabled=True)
    
    def high_cardinality(self, min_cardinality=1000):
        return self.filter(cardinality__gte=min_cardinality)