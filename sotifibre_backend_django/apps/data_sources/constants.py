# apps/data_sources/constants.py
"""
Constantes pour l'application data_sources - Version optimisée
"""

# ============================================================================
# TYPES DE SOURCES (25+)
# ============================================================================
SOURCE_TYPE_CHOICES = [
    # Fichiers
    ('excel', '📊 Excel File (.xlsx/.xls)'),
    ('csv', '📄 CSV File'),
    ('json', '🔧 JSON File'),
    ('xml', '📋 XML File'),
    ('parquet', '📦 Parquet File'),
    ('avro', '💿 Avro File'),
    
    # Bases de données relationnelles
    ('postgresql', '🐘 PostgreSQL'),
    ('mysql', '🐬 MySQL'),
    ('sqlserver', '🔷 SQL Server'),
    ('oracle', '🔶 Oracle'),
    ('sqlite', '📦 SQLite'),
    ('db2', '💾 IBM Db2'),
    
    # NoSQL
    ('mongodb', '🍃 MongoDB'),
    ('elasticsearch', '🔍 Elasticsearch'),
    ('cassandra', '⚡ Cassandra'),
    ('redis', '📀 Redis'),
    ('dynamodb', '⚙️ DynamoDB'),
    
    # Cloud Data Warehouse
    ('bigquery', '☁️ Google BigQuery'),
    ('snowflake', '❄️ Snowflake'),
    ('redshift', '🔴 Amazon Redshift'),
    ('azure_sql', '☁️ Azure SQL'),
    ('databricks', '🧪 Databricks'),
    
    # APIs
    ('rest_api', '🌐 REST API'),
    ('graphql', '⚡ GraphQL'),
    ('soap', '📨 SOAP'),
    ('odata', '📊 OData'),
    
    # Cloud Storage
    ('s3', '📦 Amazon S3'),
    ('azure_blob', '☁️ Azure Blob'),
    ('gcs', '☁️ Google Cloud Storage'),
    ('google_drive', '📁 Google Drive'),
    ('sharepoint', '📂 SharePoint'),
    ('onedrive', '💾 OneDrive'),
    
    # FTP
    ('ftp', '📁 FTP Server'),
    ('sftp', '🔒 SFTP Server'),
    
    # Streaming
    ('kafka', '📡 Apache Kafka'),
    ('kinesis', '🌊 Amazon Kinesis'),
]

# ============================================================================
# STATUTS DES SOURCES
# ============================================================================
STATUS_CHOICES = [
    ('draft', '📝 Draft'),
    ('active', '✅ Active'),
    ('inactive', '⏸️ Inactive'),
    ('error', '❌ Error'),
    ('testing', '🔍 Testing'),
    ('archived', '📦 Archived'),
    ('deprecated', '⚠️ Deprecated'),
]

# ============================================================================
# FRÉQUENCES DE RAFRAÎCHISSEMENT
# ============================================================================
REFRESH_CHOICES = [
    ('manual', '👤 Manual'),
    ('realtime', '⚡ Real-time'),
    ('every_5m', '⏱️ Every 5 Minutes'),
    ('every_15m', '🕒 Every 15 Minutes'),
    ('every_30m', '🕜 Every 30 Minutes'),
    ('hourly', '🕓 Hourly'),
    ('every_6h', '🕕 Every 6 Hours'),
    ('daily', '📅 Daily'),
    ('weekly', '📆 Weekly'),
    ('monthly', '🗓️ Monthly'),
]

# ============================================================================
# STATUTS DE TRAITEMENT DES FICHIERS
# ============================================================================
FILE_PROCESS_STATUS = [
    ('pending', '⏳ En attente'),
    ('processing', '🔄 En cours'),
    ('completed', '✅ Terminé'),
    ('failed', '❌ Échoué'),
    ('skipped', '⏭️ Ignoré'),
]

# ============================================================================
# NIVEAUX DE LOG
# ============================================================================
LOG_LEVEL_CHOICES = [
    ('info', 'ℹ️ Info'),
    ('warning', '⚠️ Warning'),
    ('error', '❌ Error'),
    ('debug', '🐛 Debug'),
]

# ============================================================================
# TYPES D'ÉTAPES POWER QUERY
# ============================================================================
QUERY_STEP_TYPES = [
    ('source', '📁 Source de données'),
    ('filter', '🔍 Filtrer les lignes'),
    ('sort', '⬆️ Trier'),
    ('group', '📊 Grouper par'),
    ('aggregate', '📈 Agréger'),
    ('merge', '🔗 Fusionner'),
    ('append', '➕ Ajouter'),
    ('pivot', '🔄 Pivoter'),
    ('unpivot', '🔄 Dépivoter'),
    ('rename', '✏️ Renommer'),
    ('remove', '🗑️ Supprimer'),
    ('split', '✂️ Diviser'),
    ('replace', '🔄 Remplacer'),
    ('transform', '⚡ Transformer'),
    ('add_column', '➕ Ajouter colonne'),
    ('change_type', '📝 Changer type'),
    ('fill', '📥 Remplir'),
    ('custom', '⚙️ Code M personnalisé'),
]

# ============================================================================
# TYPES DE BASES DE DONNÉES
# ============================================================================
DATABASE_TYPES = [
    ('postgresql', '🐘 PostgreSQL'),
    ('mysql', '🐬 MySQL'),
    ('sqlite', '📦 SQLite'),
    ('sqlserver', '🔷 SQL Server'),
    ('oracle', '🔶 Oracle'),
    ('mongodb', '🍃 MongoDB'),
    ('redis', '📀 Redis'),
    ('clickhouse', '🏠 ClickHouse'),
    ('snowflake', '❄️ Snowflake'),
    ('bigquery', '☁️ BigQuery'),
    ('redshift', '🔴 Redshift'),
    ('mariadb', '🐬 MariaDB'),
    ('cassandra', '⚡ Cassandra'),
    ('elasticsearch', '🔍 Elasticsearch'),
    ('dynamodb', '⚙️ DynamoDB'),
    ('db2', '💾 IBM Db2'),
]

# ============================================================================
# TYPES D'API
# ============================================================================
API_TYPES = [
    ('rest', 'REST'),
    ('graphql', 'GraphQL'),
    ('soap', 'SOAP'),
    ('websocket', 'WebSocket'),
    ('odata', 'OData'),
]

# ============================================================================
# TYPES DE FICHIERS
# ============================================================================
FILE_TYPES = [
    ('csv',  '📊 CSV'),
    ('xlsx', '📈 Excel (XLSX)'),
    ('yaml', '📋 YAML'),
    ('json', '🔧 JSON'),
    ('tsv',  '📑 TSV (Tabulé)'),
    ('html', '🌐 HTML'),
]

# ============================================================================
# MÉTHODES D'AUTHENTIFICATION
# ============================================================================
AUTH_TYPES = [
    ('none', '❌ Aucune'),
    ('basic', '🔑 Basic Auth'),
    ('token', '🎫 Token'),
    ('oauth2', '🔄 OAuth 2.0'),
    ('api_key', '🔑 API Key'),
    ('certificate', '📜 Certificat'),
    ('kerberos', '👑 Kerberos'),
    ('ldap', '📋 LDAP'),
]

# ============================================================================
# STATUTS DES CONNEXIONS
# ============================================================================
CONNECTION_STATUS = [
    ('active', '✅ Actif'),
    ('error', '❌ Erreur'),
    ('testing', '🔍 En test'),
    ('inactive', '⏸️ Inactif'),
    ('configuring', '⚙️ En configuration'),
    ('draft', '📝 Brouillon'),
    ('archived', '📦 Archivé'),
    ('deprecated', '⚠️ Obsolète'),
]

# ============================================================================
# FRÉQUENCES DE SYNCHRONISATION
# ============================================================================
SYNC_FREQUENCIES = [
    ('manual', '👤 Manuel'),
    ('realtime', '⚡ Temps réel'),
    ('every_5m', '⏱️ 5 minutes'),
    ('every_15m', '🕒 15 minutes'),
    ('every_30m', '🕜 30 minutes'),
    ('hourly', '🕓 Horaire'),
    ('every_6h', '🕕 6 heures'),
    ('daily', '📅 Quotidien'),
    ('weekly', '📆 Hebdomadaire'),
    ('monthly', '🗓️ Mensuel'),
]

# ============================================================================
# TYPES DE REQUÊTES
# ============================================================================
QUERY_TYPES = [
    ('sql', '📊 SQL'),
    ('nosql', '🍃 NoSQL'),
    ('rest', '🌐 REST API'),
    ('graphql', '⚡ GraphQL'),
    ('soap', '📨 SOAP'),
    ('custom', '🔧 Personnalisé'),
]

# ============================================================================
# PORTS PAR DÉFAUT
# ============================================================================
DEFAULT_PORTS = {
    'postgresql': 5432,
    'mysql': 3306,
    'sqlite': None,
    'sqlserver': 1433,
    'oracle': 1521,
    'mongodb': 27017,
    'redis': 6379,
    'clickhouse': 8123,
    'snowflake': 443,
    'bigquery': 443,
    'redshift': 5439,
    'mariadb': 3306,
    'cassandra': 9042,
    'elasticsearch': 9200,
    'db2': 50000,
}

# ============================================================================
# TIMEOUTS PAR DÉFAUT
# ============================================================================
DEFAULT_TIMEOUTS = {
    'connection': 30,
    'query': 60,
    'streaming': 10,
    'batch': 300,
}

# ============================================================================
# TAILLES DE LOT
# ============================================================================
DEFAULT_BATCH_SIZES = {
    'small': 100,
    'medium': 1000,
    'large': 10000,
    'xlarge': 100000,
}

# ============================================================================
# MOTS-CLÉS SQL DANGEREUX
# ============================================================================
DANGEROUS_SQL_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
    'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
]

# ============================================================================
# MÉTRIQUES DE PERFORMANCE
# ============================================================================
PERFORMANCE_METRICS = [
    'query_time',
    'rows_returned',
    'cpu_time',
    'io_wait',
    'network_latency',
    'cache_hit_ratio',
]

# ============================================================================
# COULEURS PAR TYPE DE SOURCE
# ============================================================================
SOURCE_TYPE_COLORS = {
    'excel': '#1f7b4d',
    'csv': '#28a745',
    'json': '#ffc107',
    'xml': '#6c757d',
    'postgresql': '#336791',
    'mysql': '#00758f',
    'sqlserver': '#cc2927',
    'oracle': '#f80000',
    'mongodb': '#4db33d',
    'redis': '#dc382d',
    'bigquery': '#4285f4',
    'snowflake': '#29b5e8',
    'redshift': '#dc5b3e',
    'rest_api': '#17a2b8',
    'graphql': '#e10098',
    's3': '#ff9900',
    'kafka': '#231f20',
    'kinesis': '#ff9900',
}