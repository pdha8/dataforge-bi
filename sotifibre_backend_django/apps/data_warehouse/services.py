# apps/data_warehouse/services.py
"""
Services pour l'application data_warehouse
"""
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db import connection, connections
from django.core.cache import cache

from apps.core.utils import Timer
from .models import StarSchema, DataWarehouseTable, DataWarehouseLog, DataWarehouseMetric

logger = logging.getLogger(__name__)


class StarSchemaService:
    """Service d'exécution des schémas en étoile"""
    
    def __init__(self, star_schema: StarSchema):
        self.star_schema = star_schema
        self.warehouse_connection = 'data_warehouse'
    
    def execute(self, limit: int = None, params: Dict = None) -> Dict[str, Any]:
        """Exécute la requête du schéma en étoile"""
        timer = Timer()
        timer.start()
        
        try:
            query = self.star_schema.generate_query()
            
            if limit:
                query += f" LIMIT {limit}"
            
            # Exécuter sur la base data_warehouse
            with connections[self.warehouse_connection].cursor() as cursor:
                cursor.execute(query, params or {})
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            timer.stop()
            
            # Mettre à jour les statistiques
            self.star_schema.query_count += 1
            self.star_schema.last_queried_at = timezone.now()
            
            total_time = self.star_schema.avg_query_time_ms * (self.star_schema.query_count - 1)
            self.star_schema.avg_query_time_ms = (total_time + timer.duration_ms()) / self.star_schema.query_count
            self.star_schema.save()
            
            # Enregistrer le log
            DataWarehouseLog.objects.create(
                table=None,
                operation='query',
                level='info',
                message=f"Exécution du schéma en étoile '{self.star_schema.name}'",
                duration_ms=timer.duration_ms(),
                rows_affected=len(rows),
                query=query,
                metadata={'star_schema_id': str(self.star_schema.id)}
            )
            
            return {
                'success': True,
                'data': rows,
                'columns': columns,
                'row_count': len(rows),
                'duration_ms': timer.duration_ms(),
                'from_cache': False
            }
            
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur exécution schéma en étoile {self.star_schema.name}: {e}")
            
            DataWarehouseLog.objects.create(
                table=None,
                operation='query',
                level='error',
                message=f"Erreur exécution schéma en étoile: {str(e)}",
                duration_ms=timer.duration_ms(),
                query=query,
                metadata={'star_schema_id': str(self.star_schema.id), 'error': str(e)},
                stack_trace=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'duration_ms': timer.duration_ms()
            }


class DataWarehouseService:
    """Service de gestion du Data Warehouse"""
    
    def __init__(self):
        self.warehouse_connection = 'data_warehouse'
    
    def execute_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Exécute une requête sur le Data Warehouse"""
        timer = Timer()
        timer.start()
        
        try:
            with connections[self.warehouse_connection].cursor() as cursor:
                cursor.execute(query, params or {})
                
                if query.strip().upper().startswith('SELECT'):
                    columns = [col[0] for col in cursor.description]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    
                    return {
                        'success': True,
                        'data': rows,
                        'columns': columns,
                        'row_count': len(rows),
                        'duration_ms': timer.duration_ms()
                    }
                else:
                    return {
                        'success': True,
                        'row_count': cursor.rowcount,
                        'duration_ms': timer.duration_ms()
                    }
                    
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur exécution requête DW: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_ms': timer.duration_ms()
            }
    
    def refresh_table(self, table: DataWarehouseTable) -> Dict[str, Any]:
        """Rafraîchit une table du Data Warehouse"""
        if not table.source_pipeline:
            return {'success': False, 'error': 'Aucun pipeline source configuré'}
        
        timer = Timer()
        timer.start()
        
        try:
            # Exécuter le pipeline source
            from apps.etl_engine.services import ETLPipelineService
            service = ETLPipelineService(table.source_pipeline)
            result = service.execute()
            
            if result['success']:
                table.last_refresh = timezone.now()
                table.refresh_duration_ms = timer.duration_ms()
                table.row_count = result.get('rows_written', 0)
                table.save()
                
                DataWarehouseLog.objects.create(
                    table=table,
                    operation='refresh',
                    level='info',
                    message=f"Table rafraîchie avec succès",
                    duration_ms=timer.duration_ms(),
                    rows_affected=table.row_count
                )
                
                return {
                    'success': True,
                    'rows_processed': table.row_count,
                    'duration_ms': timer.duration_ms()
                }
            else:
                raise Exception(result.get('error', 'Erreur inconnue'))
                
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur rafraîchissement table {table.name}: {e}")
            
            DataWarehouseLog.objects.create(
                table=table,
                operation='refresh',
                level='error',
                message=f"Erreur rafraîchissement: {str(e)}",
                duration_ms=timer.duration_ms(),
                stack_trace=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'duration_ms': timer.duration_ms()
            }
    
    def analyze_table(self, table: DataWarehouseTable) -> Dict[str, Any]:
        """Analyse une table (statistiques)"""
        timer = Timer()
        timer.start()
        
        try:
            # Collecter les statistiques
            with connections[self.warehouse_connection].cursor() as cursor:
                # Nombre de lignes
                cursor.execute(f"SELECT COUNT(*) FROM {table.full_name}")
                row_count = cursor.fetchone()[0]
                
                # Taille de la table
                cursor.execute(f"""
                    SELECT pg_total_relation_size('{table.full_name}') as size,
                           pg_indexes_size('{table.full_name}') as index_size
                """)
                result = cursor.fetchone()
                table_size = result[0] or 0
                index_size = result[1] or 0
                
                # Mettre à jour la table
                table.row_count = row_count
                table.size_bytes = table_size
                table.save(update_fields=['row_count', 'size_bytes'])
                
                # Créer la métrique
                DataWarehouseMetric.objects.create(
                    table=table,
                    table_size_bytes=table_size,
                    index_size_bytes=index_size,
                    rows_scanned=row_count
                )
                
                timer.stop()
                
                DataWarehouseLog.objects.create(
                    table=table,
                    operation='analyze',
                    level='info',
                    message=f"Table analysée",
                    duration_ms=timer.duration_ms(),
                    rows_affected=row_count
                )
                
                return {
                    'success': True,
                    'row_count': row_count,
                    'table_size_bytes': table_size,
                    'table_size_mb': round(table_size / (1024 * 1024), 2),
                    'index_size_bytes': index_size,
                    'index_size_mb': round(index_size / (1024 * 1024), 2),
                    'duration_ms': timer.duration_ms()
                }
                
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur analyse table {table.name}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'duration_ms': timer.duration_ms()
            }
    
    def optimize_table(self, table: DataWarehouseTable) -> Dict[str, Any]:
        """Optimise une table (VACUUM, ANALYZE)"""
        timer = Timer()
        timer.start()
        
        try:
            with connections[self.warehouse_connection].cursor() as cursor:
                cursor.execute(f"VACUUM ANALYZE {table.full_name}")
            
            timer.stop()
            
            DataWarehouseLog.objects.create(
                table=table,
                operation='optimize',
                level='info',
                message=f"Table optimisée",
                duration_ms=timer.duration_ms()
            )
            
            return {
                'success': True,
                'duration_ms': timer.duration_ms()
            }
            
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur optimisation table {table.name}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'duration_ms': timer.duration_ms()
            }
    
    def get_schema_stats(self, schema_name: str = None) -> Dict[str, Any]:
        """Récupère les statistiques du schéma"""
        try:
            with connections[self.warehouse_connection].cursor() as cursor:
                query = """
                    SELECT 
                        schemaname,
                        COUNT(*) as table_count,
                        SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                """
                if schema_name:
                    query += f" AND schemaname = '{schema_name}'"
                query += " GROUP BY schemaname"
                
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return {
                    'success': True,
                    'data': rows,
                    'columns': columns
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }