# apps/etl_engine/managers.py
"""
Gestionnaires personnalisés pour les modèles etl_engine
"""
from django.db import models
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta


class ETLPipelineManager(models.Manager):
    """Gestionnaire personnalisé pour ETLPipeline"""
    
    def active(self):
        """Pipelines actifs"""
        return self.filter(status='active')
    
    def by_type(self, pipeline_type):
        """Pipelines par type"""
        return self.filter(pipeline_type=pipeline_type)
    
    def by_source(self, source):
        """Pipelines par source"""
        return self.filter(source=source)
    
    def by_target(self, target):
        """Pipelines par cible"""
        return self.filter(target=target)
    
    def needs_execution(self):
        """Pipelines nécessitant une exécution"""
        need_execution = []
        for pipeline in self.filter(status='active', schedule_enabled=True):
            if not pipeline.last_execution:
                need_execution.append(pipeline.id)
                continue
            
            delta = timezone.now() - pipeline.last_execution
            intervals = {
                'every_5m': timedelta(minutes=5),
                'every_15m': timedelta(minutes=15),
                'every_30m': timedelta(minutes=30),
                'hourly': timedelta(hours=1),
                'every_6h': timedelta(hours=6),
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30),
            }
            
            if pipeline.schedule_frequency in intervals:
                if delta >= intervals[pipeline.schedule_frequency]:
                    need_execution.append(pipeline.id)
        
        return self.filter(id__in=need_execution)
    
    def with_errors(self):
        """Pipelines avec erreurs"""
        return self.filter(status='error')
    
    def stats(self):
        """Statistiques globales"""
        total = self.count()
        active = self.filter(status='active').count()
        error = self.filter(status='error').count()
        
        by_type = dict(
            self.values_list('pipeline_type').annotate(count=Count('id'))
        )
        
        total_executions = self.aggregate(Sum('execution_count'))['execution_count__sum'] or 0
        avg_duration = self.aggregate(Avg('avg_duration_seconds'))['avg_duration_seconds__avg'] or 0
        
        return {
            'total': total,
            'active': active,
            'error': error,
            'by_type': by_type,
            'total_executions': total_executions,
            'avg_duration_seconds': round(avg_duration, 2),
        }


class ExecutionLogManager(models.Manager):
    """Gestionnaire personnalisé pour ExecutionLog"""
    
    def recent(self, hours=24):
        """Logs récents"""
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.filter(started_at__gte=cutoff)
    
    def failed(self):
        """Exécutions échouées"""
        return self.filter(status='failed')
    
    def completed(self):
        """Exécutions réussies"""
        return self.filter(status='completed')
    
    def by_pipeline(self, pipeline):
        """Logs d'un pipeline"""
        return self.filter(pipeline=pipeline)
    
    def average_duration(self, pipeline):
        """Durée moyenne d'exécution"""
        return self.filter(pipeline=pipeline, status='completed').aggregate(
            avg_duration=Avg('duration_seconds')
        )['avg_duration'] or 0
    
    def success_rate(self, pipeline):
        """Taux de succès"""
        total = self.filter(pipeline=pipeline).count()
        if total == 0:
            return 100.0
        success = self.filter(pipeline=pipeline, status='completed').count()
        return (success / total) * 100