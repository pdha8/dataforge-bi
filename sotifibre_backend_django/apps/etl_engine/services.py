# apps/etl_engine/services.py
"""
Services pour l'application etl_engine
"""
import logging
import uuid
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.utils import timezone
from django.core.cache import cache

from apps.core.utils import Timer
from apps.data_sources.services import DataSourceService
from .models import ETLPipeline, Transformation, ExecutionLog

logger = logging.getLogger(__name__)


class ETLPipelineService:
    """Service d'exécution des pipelines ETL"""
    
    def __init__(self, pipeline: ETLPipeline):
        self.pipeline = pipeline
        self.execution = None
        self.source_service = None
        self.target_service = None
    
    def execute(self, params: Dict = None, triggered_by: str = 'manual', user=None) -> Dict[str, Any]:
        """Exécute le pipeline ETL"""
        
        # Créer l'exécution
        execution_id = str(uuid.uuid4())
        self.execution = ExecutionLog.objects.create(
            pipeline=self.pipeline,
            execution_id=execution_id,
            status='running',
            triggered_by=triggered_by,
            triggered_by_user=user,
            execution_metadata={'params': params or {}}
        )
        
        timer = Timer()
        timer.start()
        
        try:
            # Initialiser les services source et cible
            if self.pipeline.source:
                self.source_service = DataSourceService(self.pipeline.source)
                if not self.source_service.data_source.is_connected:
                    raise Exception("Source non connectée")
            
            if self.pipeline.target:
                self.target_service = DataSourceService(self.pipeline.target)
                if not self.target_service.data_source.is_connected:
                    raise Exception("Cible non connectée")
            
            # Étape 1: Extraction
            self.execution.add_transformation_log('extract', 'running')
            data = self._extract(params)
            self.execution.rows_read = len(data) if isinstance(data, list) else 0
            self.execution.add_transformation_log('extract', 'completed', {'rows': self.execution.rows_read})
            
            # Étape 2: Transformations
            self.execution.add_transformation_log('transform', 'running')
            data = self._transform(data, params)
            self.execution.add_transformation_log('transform', 'completed', {'rows': len(data) if isinstance(data, list) else 0})
            
            # Étape 3: Chargement
            self.execution.add_transformation_log('load', 'running')
            result = self._load(data, params)
            self.execution.rows_written = result.get('rows_written', 0)
            self.execution.add_transformation_log('load', 'completed', {'rows_written': self.execution.rows_written})
            
            # Succès
            timer.stop()
            self.execution.complete(success=True)
            
            # Mettre à jour les métriques du pipeline
            self.pipeline.update_metrics(
                duration_seconds=timer.duration(),
                rows_processed=self.execution.rows_written,
                success=True
            )
            
            # Notifications de succès
            if self.pipeline.notify_on_success:
                self._send_notifications(success=True)
            
            return {
                'success': True,
                'execution_id': execution_id,
                'rows_read': self.execution.rows_read,
                'rows_written': self.execution.rows_written,
                'duration_seconds': timer.duration(),
                'result': result.get('data', {})
            }
            
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur exécution pipeline {self.pipeline.name}: {e}")
            
            self.execution.complete(success=False)
            self.execution.error_message = str(e)[:2000]
            self.execution.save()
            
            # Mettre à jour les métriques du pipeline
            self.pipeline.update_metrics(
                duration_seconds=timer.duration() or 0,
                rows_processed=0,
                success=False
            )
            
            # Notifications d'échec
            if self.pipeline.notify_on_failure:
                self._send_notifications(success=False, error=str(e))
            
            return {
                'success': False,
                'execution_id': execution_id,
                'error': str(e),
                'duration_seconds': timer.duration()
            }
    
    def _extract(self, params: Dict = None) -> Any:
        """Extrait les données de la source"""
        if not self.source_service:
            return []
        
        # Construire la requête
        if self.pipeline.source_schema:
            schema = self.pipeline.source_schema
            
            if schema.query:
                query = schema.query
            elif schema.table_name:
                query = f"SELECT * FROM {schema.table_name}"
                if schema.filters:
                    # Appliquer les filtres
                    pass
                if schema.selected_columns:
                    columns = ', '.join(schema.selected_columns)
                    query = f"SELECT {columns} FROM {schema.table_name}"
            else:
                query = None
            
            if query:
                result = self.source_service.execute_query(query, params)
                if result['success']:
                    return result.get('data', [])
                else:
                    raise Exception(f"Erreur extraction: {result.get('error')}")
        
        return []
    
    def _transform(self, data: Any, params: Dict = None) -> Any:
        """Applique les transformations"""
        if not data:
            return data
        
        df = pd.DataFrame(data) if isinstance(data, list) else data
        
        # Appliquer chaque transformation dans l'ordre
        for trans in self.pipeline.transformation_list.filter(is_enabled=True).order_by('order'):
            try:
                timer = Timer()
                timer.start()
                
                df = self._apply_transformation(df, trans, params)
                
                timer.stop()
                trans.update_metrics(timer.duration_ms(), success=True)
                
                self.execution.add_transformation_log(
                    trans.name, 'completed',
                    {'duration_ms': timer.duration_ms(), 'rows': len(df)}
                )
                
            except Exception as e:
                trans.update_metrics(0, success=False)
                trans.last_error = str(e)[:500]
                trans.save()
                
                self.execution.add_transformation_log(
                    trans.name, 'failed', {'error': str(e)}
                )
                
                if trans.is_critical or self.pipeline.error_strategy == 'fail':
                    raise Exception(f"Transformation {trans.name} échouée: {e}")
                elif self.pipeline.error_strategy == 'skip':
                    continue
                elif self.pipeline.error_strategy == 'default':
                    # Utiliser la valeur par défaut
                    pass
        
        return df.to_dict('records') if isinstance(df, pd.DataFrame) else df
    
    def _apply_transformation(self, df: pd.DataFrame, transformation: Transformation, params: Dict) -> pd.DataFrame:
        """Applique une transformation spécifique"""
        
        trans_type = transformation.transformation_type
        config = transformation.config
        
        if trans_type == 'filter':
            # Filtrer les lignes
            column = config.get('column')
            operator = config.get('operator')
            value = config.get('value')
            
            if operator == 'eq':
                df = df[df[column] == value]
            elif operator == 'gt':
                df = df[df[column] > value]
            elif operator == 'lt':
                df = df[df[column] < value]
            # ... autres opérateurs
        
        elif trans_type == 'select':
            # Sélectionner des colonnes
            columns = config.get('columns', [])
            if columns:
                df = df[columns]
        
        elif trans_type == 'rename':
            # Renommer des colonnes
            mapping = config.get('mapping', {})
            df = df.rename(columns=mapping)
        
        elif trans_type == 'cast':
            # Changer le type
            for col, dtype in config.get('types', {}).items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype)
        
        elif trans_type == 'aggregate':
            # Agréger
            group_by = config.get('group_by', [])
            aggregations = config.get('aggregations', {})
            df = df.groupby(group_by).agg(aggregations).reset_index()
        
        elif trans_type == 'join':
            # Joindre avec une autre source
            pass
        
        elif trans_type == 'custom_python':
            # Code Python personnalisé
            if transformation.custom_code:
                exec_globals = {'df': df, 'params': params}
                exec(transformation.custom_code, exec_globals)
                df = exec_globals.get('df', df)
        
        elif trans_type == 'custom_sql':
            # SQL personnalisé
            pass
        
        elif trans_type == 'deduplicate':
            # Supprimer les doublons
            subset = config.get('subset', None)
            keep = config.get('keep', 'first')
            df = df.drop_duplicates(subset=subset, keep=keep)
        
        elif trans_type == 'fillna':
            # Remplir les valeurs nulles
            value = config.get('value', 0)
            columns = config.get('columns', None)
            if columns:
                for col in columns:
                    if col in df.columns:
                        df[col] = df[col].fillna(value)
            else:
                df = df.fillna(value)
        
        elif trans_type == 'dropna':
            # Supprimer les lignes avec valeurs nulles
            subset = config.get('subset', None)
            how = config.get('how', 'any')
            df = df.dropna(subset=subset, how=how)
        
        elif trans_type == 'sort':
            # Trier
            by = config.get('by', [])
            ascending = config.get('ascending', True)
            if by:
                df = df.sort_values(by=by, ascending=ascending)
        
        return df
    
    def _load(self, data: Any, params: Dict = None) -> Dict[str, Any]:
        """Charge les données dans la cible"""
        if not self.target_service:
            return {'rows_written': len(data) if isinstance(data, list) else 0}
        
        if not data:
            return {'rows_written': 0}
        
        # Convertir en liste de dictionnaires si nécessaire
        if isinstance(data, pd.DataFrame):
            data = data.to_dict('records')
        
        # Déterminer la stratégie d'insertion
        insert_strategy = 'append'
        if self.pipeline.target_schema:
            insert_strategy = self.pipeline.target_schema.insert_strategy
        
        # Construire la requête d'insertion
        table_name = self.pipeline.target_schema.table_name if self.pipeline.target_schema else 'data'
        columns = list(data[0].keys()) if data else []
        
        if insert_strategy == 'append':
            # INSERT INTO
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
        elif insert_strategy == 'upsert':
            # INSERT ... ON CONFLICT
            upsert_keys = self.pipeline.target_schema.upsert_keys
            update_cols = [col for col in columns if col not in upsert_keys]
            update_set = ', '.join([f"{col}=EXCLUDED.{col}" for col in update_cols])
            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(['%s'] * len(columns))})
                ON CONFLICT ({', '.join(upsert_keys)})
                DO UPDATE SET {update_set}
            """
        else:
            query = None
        
        if query:
            # Exécuter les insertions
            rows_written = 0
            for row in data:
                values = [row.get(col) for col in columns]
                result = self.target_service.execute_query(query, values)
                if result['success']:
                    rows_written += 1
            
            return {'rows_written': rows_written}
        
        return {'rows_written': len(data)}
    
    def _send_notifications(self, success: bool = True, error: str = None):
        """Envoie les notifications"""
        if not self.pipeline.notifications_enabled:
            return
        
        for notification in self.pipeline.notifications.all():
            if success and not notification.send_on_success:
                continue
            if not success and not notification.send_on_failure:
                continue
            
            if notification.channel == 'email':
                self._send_email_notification(notification, success, error)
            elif notification.channel == 'slack':
                self._send_slack_notification(notification, success, error)
            # ... autres canaux
    
    def _send_email_notification(self, notification, success, error):
        """Envoie une notification email"""
        # À implémenter
        pass
    
    def _send_slack_notification(self, notification, success, error):
        """Envoie une notification Slack"""
        # À implémenter
        pass


class ETLOrchestrator:
    """Orchestrateur de pipelines ETL"""
    
    def __init__(self):
        self.executions = {}
    
    def execute_pipeline(self, pipeline_id, params=None, triggered_by='manual', user=None):
        """Exécute un pipeline avec ses dépendances"""
        try:
            pipeline = ETLPipeline.objects.get(id=pipeline_id)
        except ETLPipeline.DoesNotExist:
            return {'success': False, 'error': 'Pipeline non trouvé'}
        
        # Vérifier les dépendances
        if pipeline.dependencies.exists():
            for dep in pipeline.dependencies.all():
                if dep.status != 'active':
                    return {
                        'success': False,
                        'error': f'Dépendance {dep.name} non active'
                    }
        
        # Exécuter le pipeline
        service = ETLPipelineService(pipeline)
        return service.execute(params, triggered_by, user)
    
    def execute_pipelines(self, pipeline_ids, params=None, triggered_by='manual', user=None):
        """Exécute plusieurs pipelines en parallèle"""
        import concurrent.futures
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for pipeline_id in pipeline_ids:
                future = executor.submit(self.execute_pipeline, pipeline_id, params, triggered_by, user)
                futures[future] = pipeline_id
            
            for future in concurrent.futures.as_completed(futures):
                pipeline_id = futures[future]
                try:
                    results[pipeline_id] = future.result()
                except Exception as e:
                    results[pipeline_id] = {'success': False, 'error': str(e)}
        
        return results