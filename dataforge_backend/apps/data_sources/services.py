# apps/data_sources/services.py
"""
Services pour l'application data_sources - Version optimisée
"""
import logging
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.utils import timezone
from django.core.cache import cache

from apps.core.utils import Timer
from .models import DataSource, DataTable, DataQuery, DataSourceLog, DataSourceMetric
from .validators import validate_sql_query

logger = logging.getLogger(__name__)


class DataSourceService:
    """Service de gestion des sources de données"""
    
    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self._connection = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion à la source de données"""
        timer = Timer()
        timer.start()
        
        try:
            if self.data_source.source_type in ['postgresql', 'mysql', 'sqlserver', 'oracle', 'sqlite', 'db2']:
                result = self._test_database_connection()
            elif self.data_source.source_type in ['mongodb', 'elasticsearch', 'cassandra', 'redis']:
                result = self._test_nosql_connection()
            elif self.data_source.source_type in ['bigquery', 'snowflake', 'redshift', 'azure_sql', 'databricks']:
                result = self._test_cloud_dwh_connection()
            elif self.data_source.source_type in ['rest_api', 'graphql', 'soap', 'odata']:
                result = self._test_api_connection()
            elif self.data_source.source_type in ['excel', 'csv', 'json', 'xml', 'parquet', 'avro']:
                result = self._test_file_connection()
            elif self.data_source.source_type in ['s3', 'azure_blob', 'gcs', 'google_drive', 'sharepoint', 'onedrive']:
                result = self._test_cloud_storage_connection()
            elif self.data_source.source_type in ['ftp', 'sftp']:
                result = self._test_ftp_connection()
            elif self.data_source.source_type in ['kafka', 'kinesis']:
                result = self._test_streaming_connection()
            else:
                result = {'success': False, 'error': 'Type de source non supporté'}
            
            timer.stop()
            
            # Mettre à jour le statut
            if result['success']:
                self.data_source.status = 'active'
                self.data_source.last_sync = timezone.now()
                self._log('info', 'Connexion testée avec succès', execution_time_ms=timer.duration_ms())
            else:
                self.data_source.status = 'error'
                self.data_source.last_sync_error = result.get('error', 'Erreur inconnue')
                self._log('error', f"Échec de connexion: {result.get('error')}", 
                         execution_time_ms=timer.duration_ms())
            
            self.data_source.save(update_fields=['status', 'last_sync', 'last_sync_error'])
            
            return result
            
        except Exception as e:
            logger.exception(f"Erreur test connexion: {e}")
            return {'success': False, 'error': str(e)}
    
    def _test_database_connection(self) -> Dict[str, Any]:
        """Teste une connexion base de données relationnelle"""
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, text
            
            connection_string = self._build_connection_string()
            engine = create_engine(connection_string, connect_args={'connect_timeout': 10})
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                if row and row[0] == 1:
                    return {'success': True, 'message': 'Connexion réussie', 'latency_ms': 0}
            
            return {'success': False, 'error': 'La requête de test a échoué'}
            
        except ImportError:
            return {'success': False, 'error': 'SQLAlchemy non installé'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_nosql_connection(self) -> Dict[str, Any]:
        """Teste une connexion NoSQL"""
        try:
            if self.data_source.source_type == 'mongodb':
                from pymongo import MongoClient
                client = MongoClient(self._build_connection_string())
                client.admin.command('ping')
                return {'success': True, 'message': 'Connexion MongoDB réussie'}
            elif self.data_source.source_type == 'redis':
                import redis
                r = redis.Redis(
                    host=self.data_source.host,
                    port=self.data_source.port or 6379,
                    password=self.data_source.password,
                    decode_responses=True
                )
                r.ping()
                return {'success': True, 'message': 'Connexion Redis réussie'}
            else:
                return {'success': False, 'error': f'Type NoSQL non supporté: {self.data_source.source_type}'}
        except ImportError:
            return {'success': False, 'error': 'Bibliothèque NoSQL non installée'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_cloud_dwh_connection(self) -> Dict[str, Any]:
        """Teste une connexion Cloud Data Warehouse"""
        try:
            if self.data_source.source_type == 'bigquery':
                from google.cloud import bigquery
                client = bigquery.Client()
                client.query("SELECT 1").result()
                return {'success': True, 'message': 'Connexion BigQuery réussie'}
            elif self.data_source.source_type == 'snowflake':
                import snowflake.connector
                conn = snowflake.connector.connect(
                    user=self.data_source.username,
                    password=self.data_source.password,
                    account=self.data_source.host,
                    warehouse=self.data_source.database_name
                )
                conn.cursor().execute("SELECT 1")
                conn.close()
                return {'success': True, 'message': 'Connexion Snowflake réussie'}
            else:
                return {'success': False, 'error': f'Type Cloud DWH non supporté'}
        except ImportError:
            return {'success': False, 'error': 'Bibliothèque Cloud DWH non installée'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_api_connection(self) -> Dict[str, Any]:
        """Teste une connexion API"""
        try:
            import requests
            
            headers = self.data_source.api_headers or {}
            if self.data_source.auth_type == 'api_key':
                headers[self.data_source.api_key_header] = self.data_source.api_key
            elif self.data_source.auth_type == 'token':
                headers['Authorization'] = f"Bearer {self.data_source.auth_token}"
            
            url = f"{self.data_source.api_url}{self.data_source.api_endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {'success': True, 'message': 'API répond correctement', 'status_code': 200}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}", 'status_code': response.status_code}
                
        except ImportError:
            return {'success': False, 'error': 'Requests non installé'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_file_connection(self) -> Dict[str, Any]:
        """Teste une connexion fichier"""
        try:
            import os
            
            if self.data_source.file_path:
                if os.path.exists(self.data_source.file_path):
                    return {'success': True, 'message': 'Fichier trouvé', 'path': self.data_source.file_path}
                else:
                    return {'success': False, 'error': 'Fichier non trouvé', 'path': self.data_source.file_path}
            
            elif self.data_source.file_url:
                import requests
                response = requests.head(self.data_source.file_url, timeout=10)
                if response.status_code == 200:
                    return {'success': True, 'message': 'URL accessible', 'url': self.data_source.file_url}
                else:
                    return {'success': False, 'error': f"HTTP {response.status_code}", 'url': self.data_source.file_url}
            
            return {'success': False, 'error': 'Aucun chemin ou URL fourni'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_cloud_storage_connection(self) -> Dict[str, Any]:
        """Teste une connexion cloud storage"""
        try:
            if self.data_source.source_type == 's3':
                import boto3
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=self.data_source.username,
                    aws_secret_access_key=self.data_source.password,
                    region_name=self.data_source.region
                )
                s3.head_bucket(Bucket=self.data_source.bucket_name)
                return {'success': True, 'message': 'Connexion S3 réussie'}
            else:
                return {'success': False, 'error': f'Type cloud storage non supporté'}
        except ImportError:
            return {'success': False, 'error': 'Bibliothèque cloud non installée'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_ftp_connection(self) -> Dict[str, Any]:
        """Teste une connexion FTP/SFTP"""
        try:
            if self.data_source.source_type == 'ftp':
                from ftplib import FTP
                ftp = FTP(self.data_source.host)
                ftp.login(self.data_source.username, self.data_source.password)
                ftp.quit()
                return {'success': True, 'message': 'Connexion FTP réussie'}
            elif self.data_source.source_type == 'sftp':
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    self.data_source.host,
                    port=self.data_source.port or 22,
                    username=self.data_source.username,
                    password=self.data_source.password
                )
                ssh.close()
                return {'success': True, 'message': 'Connexion SFTP réussie'}
        except ImportError:
            return {'success': False, 'error': 'Bibliothèque FTP non installée'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_streaming_connection(self) -> Dict[str, Any]:
        """Teste une connexion streaming"""
        try:
            if self.data_source.source_type == 'kafka':
                from kafka import KafkaConsumer
                consumer = KafkaConsumer(
                    self.data_source.streaming_topic,
                    bootstrap_servers=self.data_source.streaming_broker,
                    request_timeout_ms=5000
                )
                consumer.close()
                return {'success': True, 'message': 'Connexion Kafka réussie'}
            else:
                return {'success': False, 'error': f'Type streaming non supporté'}
        except ImportError:
            return {'success': False, 'error': 'Bibliothèque streaming non installée'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _build_connection_string(self) -> str:
        """Construit une chaîne de connexion SQLAlchemy"""
        if self.data_source.connection_string:
            return self.data_source.connection_string
        
        if not self.data_source.database_type:
            raise ValueError("Type de base de données non spécifié")
        
        dialect_map = {
            'postgresql': 'postgresql',
            'mysql': 'mysql',
            'sqlite': 'sqlite',
            'sqlserver': 'mssql+pyodbc',
            'oracle': 'oracle',
            'mongodb': 'mongodb',
            'clickhouse': 'clickhouse',
            'db2': 'ibm_db_sa',
        }
        
        dialect = dialect_map.get(self.data_source.database_type, self.data_source.database_type)
        
        if self.data_source.database_type == 'sqlite':
            return f"sqlite:///{self.data_source.database_name}"
        
        return f"{dialect}://{self.data_source.username}:{self.data_source.password}@{self.data_source.host}:{self.data_source.port}/{self.data_source.database_name}"
    
    def execute_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Exécute une requête sur la source de données"""
        timer = Timer()
        timer.start()
        
        # Valider la requête
        try:
            validate_sql_query(query)
        except Exception as e:
            return {'success': False, 'error': f"Requête invalide: {str(e)}"}
        
        try:
            if self.data_source.is_database:
                result = self._execute_database_query(query, params)
            elif self.data_source.is_api:
                result = self._execute_api_query(query, params)
            elif self.data_source.is_file_based:
                result = self._execute_file_query(query, params)
            else:
                result = {'success': False, 'error': 'Type de source non supporté pour l\'exécution'}
            
            timer.stop()
            
            # Mettre à jour les statistiques
            self.data_source.total_queries += 1
            if result['success']:
                self.data_source.successful_queries += 1
                self.data_source.consecutive_failures = 0
            else:
                self.data_source.failed_queries += 1
                self.data_source.consecutive_failures += 1
            
            # Calculer le temps moyen
            total_time = self.data_source.avg_query_time_ms * (self.data_source.total_queries - 1)
            self.data_source.avg_query_time_ms = (total_time + timer.duration_ms()) / self.data_source.total_queries
            
            self.data_source.last_query_time = timezone.now()
            self.data_source.save()
            
            # Enregistrer la métrique
            DataSourceMetric.objects.create(
                data_source=self.data_source,
                query_time_ms=timer.duration_ms(),
                rows_returned=result.get('row_count', 0) if result['success'] else None,
            )
            
            # Enregistrer le log
            self._log(
                'info' if result['success'] else 'error',
                f"Requête exécutée: {query[:100]}...",
                query_text=query,
                execution_time_ms=timer.duration_ms(),
                rows_affected=result.get('row_count', 0) if result['success'] else None,
                data={'params': params} if params else None
            )
            
            return result
            
        except Exception as e:
            timer.stop()
            logger.exception(f"Erreur exécution requête: {e}")
            
            self._log('error', f"Erreur exécution: {str(e)}", query_text=query)
            
            return {'success': False, 'error': str(e)}
    
    def _execute_database_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Exécute une requête SQL"""
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, text
            
            connection_string = self._build_connection_string()
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                
                if query.strip().upper().startswith('SELECT'):
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    
                    return {
                        'success': True,
                        'data': rows,
                        'columns': list(columns),
                        'row_count': len(rows),
                    }
                else:
                    conn.commit()
                    return {
                        'success': True,
                        'row_count': result.rowcount,
                    }
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_api_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Exécute une requête API"""
        try:
            import requests
            
            url = f"{self.data_source.api_url}{self.data_source.api_endpoint}"
            all_params = {**self.data_source.api_params, **(params or {})}
            
            headers = self.data_source.api_headers or {}
            if self.data_source.auth_type == 'api_key':
                headers[self.data_source.api_key_header] = self.data_source.api_key
            elif self.data_source.auth_type == 'token':
                headers['Authorization'] = f"Bearer {self.data_source.auth_token}"
            
            response = requests.get(url, headers=headers, params=all_params, timeout=self.data_source.timeout_seconds)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'status_code': response.status_code,
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'status_code': response.status_code,
                    'response': response.text[:500],
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_file_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """
        Exécute une lecture de fichier.

        Formats supportés : CSV, Excel (xlsx/xls), JSON, Parquet, YAML, TSV, HTML, XML.
        Pour HTML, retourne la première table trouvée.
        """
        try:
            file_format = (query.lower() if query else self.data_source.file_type or '').strip().lower()
            file_path = self.data_source.file_path
            encoding = self.data_source.file_encoding or 'utf-8'

            if not file_path:
                return {'success': False, 'error': 'Aucun fichier configuré'}

            if file_format == 'csv':
                delimiter = getattr(self.data_source, 'delimiter', ',') or ','
                df = pd.read_csv(file_path, encoding=encoding, sep=delimiter)
            elif file_format in ('excel', 'xlsx', 'xls'):
                df = pd.read_excel(file_path, sheet_name=self.data_source.sheet_name or 0)
            elif file_format == 'json':
                df = pd.read_json(file_path, encoding=encoding)
            elif file_format == 'parquet':
                df = pd.read_parquet(file_path)
            elif file_format == 'tsv':
                df = pd.read_csv(file_path, encoding=encoding, sep='\t')
            elif file_format in ('yaml', 'yml'):
                import yaml
                with open(file_path, 'r', encoding=encoding) as f:
                    payload = yaml.safe_load(f)
                # Normaliser : si dict racine avec clé "data" / "items" / "records", l'utiliser
                if isinstance(payload, dict):
                    for key in ('data', 'items', 'records', 'rows'):
                        if key in payload and isinstance(payload[key], list):
                            payload = payload[key]
                            break
                df = pd.json_normalize(payload) if isinstance(payload, list) else pd.DataFrame([payload])
            elif file_format == 'html':
                tables = pd.read_html(file_path, encoding=encoding)
                if not tables:
                    return {'success': False, 'error': 'Aucune table HTML trouvée dans le fichier'}
                # Si params['table_index'] fourni, on prend cette table, sinon la première
                idx = (params or {}).get('table_index', 0)
                df = tables[idx] if 0 <= idx < len(tables) else tables[0]
            elif file_format == 'xml':
                df = pd.read_xml(file_path, encoding=encoding)
            else:
                return {'success': False, 'error': f"Format non supporté: {file_format}"}

            # Appliquer les filtres
            if params and 'filter' in params and isinstance(params['filter'], dict):
                for col, val in params['filter'].items():
                    if col in df.columns:
                        df = df[df[col] == val]

            # Limiter le nombre de lignes
            limit = params.get('limit', 1000) if params else 1000
            df = df.head(limit)

            return {
                'success': True,
                'data': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'row_count': len(df),
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _log(self, level: str, message: str, **kwargs):
        """Enregistre un log"""
        DataSourceLog.objects.create(
            data_source=self.data_source,
            level=level,
            message=message,
            **kwargs
        )
    
    def sync_tables(self) -> Dict[str, Any]:
        """Synchronise la liste des tables de la source"""
        if not self.data_source.is_connected:
            return {'success': False, 'error': 'Source non connectée'}
        
        try:
            if self.data_source.is_database:
                return self._sync_database_tables()
            return {'success': False, 'error': 'Type de source non supporté pour la synchronisation des tables'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _sync_database_tables(self) -> Dict[str, Any]:
        """Synchronise les tables d'une base de données"""
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, inspect
            
            connection_string = self._build_connection_string()
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            tables_created = 0
            tables_updated = 0
            
            for table_name in inspector.get_table_names():
                columns = []
                for column in inspector.get_columns(table_name):
                    columns.append({
                        'name': column['name'],
                        'type': str(column['type']),
                        'nullable': column.get('nullable', True),
                        'default': str(column.get('default')) if column.get('default') else None,
                    })
                
                primary_key = inspector.get_pk_constraint(table_name)
                indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
                foreign_keys = [fk['referred_table'] for fk in inspector.get_foreign_keys(table_name)]
                
                table, created = DataTable.objects.update_or_create(
                    data_source=self.data_source,
                    name=table_name,
                    defaults={
                        'columns': columns,
                        'primary_key': primary_key.get('constrained_columns', []),
                        'indexes': indexes,
                        'foreign_keys': foreign_keys,
                        'last_analyzed': timezone.now(),
                    }
                )
                
                if created:
                    tables_created += 1
                else:
                    tables_updated += 1
            
            return {
                'success': True,
                'tables_created': tables_created,
                'tables_updated': tables_updated,
                'total_tables': tables_created + tables_updated
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class QueryService:
    """Service de gestion des requêtes enregistrées"""
    
    def __init__(self, query: DataQuery):
        self.query = query
        self.data_source_service = DataSourceService(query.data_source)
    
    def execute(self, params: Dict = None) -> Dict[str, Any]:
        """Exécute la requête avec gestion du cache"""
        # Vérifier le cache
        cache_key = f"query_{self.query.id}_{hash(str(params))}"
        cached = cache.get(cache_key)
        
        if cached and self._is_cache_valid():
            return {
                'success': True,
                'data': cached,
                'from_cache': True,
            }
        
        # Exécuter la requête
        # NB: DataQuery.parameters est typé default=list côté modèle — on retombe
        # sur un dict vide si ce n'est pas un mapping, sinon le ** unpack lèverait TypeError.
        stored_params = self.query.parameters if isinstance(self.query.parameters, dict) else {}
        result = self.data_source_service.execute_query(
            self.query.query_text,
            {**stored_params, **(params or {})}
        )
        
        # Mettre à jour les statistiques
        self.query.execution_count += 1
        
        if result['success']:
            self.query.last_executed = timezone.now()
            self.query.avg_execution_time_ms = (
                (self.query.avg_execution_time_ms * (self.query.execution_count - 1) + 
                 result.get('execution_time_ms', 0)) / self.query.execution_count
            )
            
            # Mettre en cache
            if self.query.is_cached:
                cache.set(cache_key, result.get('data'), self.query.cache_ttl)
                self.query.cached_result = result.get('data', {})
                self.query.cached_at = timezone.now()
        
        self.query.save()
        
        return result
    
    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache est valide"""
        if not self.query.is_cached or not self.query.cached_at:
            return False
        
        delta = timezone.now() - self.query.cached_at
        return delta.total_seconds() < self.query.cache_ttl
    
    def clear_cache(self):
        """Vide le cache de la requête"""
        self.query.clear_cache()
        cache.delete_pattern(f"query_{self.query.id}_*")