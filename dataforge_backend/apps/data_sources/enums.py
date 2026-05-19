# apps/data_sources/enums.py
"""
Enums pour l'application data_sources
"""
from enum import Enum


class DataSourceType(str, Enum):
    """Types de sources de données"""
    EXCEL = 'excel'
    CSV = 'csv'
    JSON = 'json'
    XML = 'xml'
    PARQUET = 'parquet'
    AVRO = 'avro'
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLSERVER = 'sqlserver'
    ORACLE = 'oracle'
    SQLITE = 'sqlite'
    DB2 = 'db2'
    MONGODB = 'mongodb'
    ELASTICSEARCH = 'elasticsearch'
    CASSANDRA = 'cassandra'
    REDIS = 'redis'
    DYNAMODB = 'dynamodb'
    BIGQUERY = 'bigquery'
    SNOWFLAKE = 'snowflake'
    REDSHIFT = 'redshift'
    AZURE_SQL = 'azure_sql'
    DATABRICKS = 'databricks'
    REST_API = 'rest_api'
    GRAPHQL = 'graphql'
    SOAP = 'soap'
    ODATA = 'odata'
    S3 = 's3'
    AZURE_BLOB = 'azure_blob'
    GCS = 'gcs'
    GOOGLE_DRIVE = 'google_drive'
    SHAREPOINT = 'sharepoint'
    ONEDRIVE = 'onedrive'
    FTP = 'ftp'
    SFTP = 'sftp'
    KAFKA = 'kafka'
    KINESIS = 'kinesis'


class DatabaseType(str, Enum):
    """Types de bases de données"""
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLITE = 'sqlite'
    SQLSERVER = 'sqlserver'
    ORACLE = 'oracle'
    MONGODB = 'mongodb'
    REDIS = 'redis'
    CLICKHOUSE = 'clickhouse'
    SNOWFLAKE = 'snowflake'
    BIGQUERY = 'bigquery'
    REDSHIFT = 'redshift'
    MARIADB = 'mariadb'
    CASSANDRA = 'cassandra'
    ELASTICSEARCH = 'elasticsearch'
    DYNAMODB = 'dynamodb'
    DB2 = 'db2'


class ConnectionStatus(str, Enum):
    """Statuts de connexion"""
    ACTIVE = 'active'
    ERROR = 'error'
    TESTING = 'testing'
    INACTIVE = 'inactive'
    CONFIGURING = 'configuring'
    DRAFT = 'draft'
    ARCHIVED = 'archived'
    DEPRECATED = 'deprecated'


class SyncFrequency(str, Enum):
    """Fréquences de synchronisation"""
    MANUAL = 'manual'
    REALTIME = 'realtime'
    EVERY_5M = 'every_5m'
    EVERY_15M = 'every_15m'
    EVERY_30M = 'every_30m'
    HOURLY = 'hourly'
    EVERY_6H = 'every_6h'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


class QueryType(str, Enum):
    """Types de requêtes"""
    SQL = 'sql'
    NOSQL = 'nosql'
    REST = 'rest'
    GRAPHQL = 'graphql'
    SOAP = 'soap'
    CUSTOM = 'custom'


class AuthType(str, Enum):
    """Types d'authentification"""
    NONE = 'none'
    BASIC = 'basic'
    TOKEN = 'token'
    OAUTH2 = 'oauth2'
    API_KEY = 'api_key'
    CERTIFICATE = 'certificate'
    KERBEROS = 'kerberos'
    LDAP = 'ldap'


class FileType(str, Enum):
    """Types de fichiers"""
    CSV = 'csv'
    EXCEL = 'excel'
    JSON = 'json'
    PARQUET = 'parquet'
    AVRO = 'avro'
    ORC = 'orc'
    XML = 'xml'
    TXT = 'txt'