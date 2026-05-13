# apps/etl_engine/constants.py
"""
Constantes pour l'application etl_engine
"""

# ============================================================================
# TYPES DE PIPELINES
# ============================================================================
PIPELINE_TYPES = [
    ('extract', '📤 Extract Only'),
    ('load', '📥 Load Only'),
    ('etl', '🔄 ETL (Extract-Transform-Load)'),
    ('elt', '🔄 ELT (Extract-Load-Transform)'),
    ('replication', '📋 Replication'),
    ('migration', '🚚 Migration'),
    ('aggregation', '📊 Aggregation'),
    ('cleaning', '🧹 Data Cleaning'),
]

# ============================================================================
# STATUTS DES PIPELINES
# ============================================================================
PIPELINE_STATUS = [
    ('draft', '📝 Draft'),
    ('active', '✅ Active'),
    ('paused', '⏸️ Paused'),
    ('error', '❌ Error'),
    ('archived', '📦 Archived'),
    ('deprecated', '⚠️ Deprecated'),
]

# ============================================================================
# STATUTS DES EXÉCUTIONS
# ============================================================================
EXECUTION_STATUS = [
    ('pending', '⏳ Pending'),
    ('running', '🔄 Running'),
    ('completed', '✅ Completed'),
    ('failed', '❌ Failed'),
    ('cancelled', '🚫 Cancelled'),
    ('skipped', '⏭️ Skipped'),
    ('retrying', '🔄 Retrying'),
]

# ============================================================================
# TYPES DE TRANSFORMATIONS
# ============================================================================
TRANSFORMATION_TYPES = [
    ('filter', '🔍 Filter Rows'),
    ('select', '📋 Select Columns'),
    ('rename', '✏️ Rename Columns'),
    ('cast', '📝 Cast Data Type'),
    ('aggregate', '📊 Aggregate'),
    ('join', '🔗 Join'),
    ('union', '➕ Union'),
    ('sort', '⬆️ Sort'),
    ('group_by', '📊 Group By'),
    ('pivot', '🔄 Pivot'),
    ('unpivot', '🔄 Unpivot'),
    ('window', '📈 Window Function'),
    ('custom_sql', '⚙️ Custom SQL'),
    ('custom_python', '🐍 Custom Python'),
    ('validation', '✅ Validation'),
    ('deduplicate', '🗑️ Deduplicate'),
    ('fillna', '📥 Fill Nulls'),
    ('dropna', '🗑️ Drop Nulls'),
    ('normalize', '📐 Normalize'),
    ('encode', '🔢 Encode'),
    ('split', '✂️ Split Column'),
    ('merge', '🔗 Merge Columns'),
]

# ============================================================================
# STRATÉGIES DE GESTION DES ERREURS
# ============================================================================
ERROR_STRATEGIES = [
    ('fail', '❌ Fail Pipeline'),
    ('skip', '⏭️ Skip Row'),
    ('default', '📝 Use Default Value'),
    ('retry', '🔄 Retry'),
    ('notify', '🔔 Notify Only'),
    ('continue', '▶️ Continue'),
]

# ============================================================================
# MODES DE TRAITEMENT
# ============================================================================
PROCESSING_MODES = [
    ('batch', '📦 Batch'),
    ('streaming', '📡 Streaming'),
    ('incremental', '📈 Incremental'),
    ('full', '🔄 Full Refresh'),
]

# ============================================================================
# NIVEAUX DE LOG
# ============================================================================
LOG_LEVELS = [
    ('debug', '🐛 Debug'),
    ('info', 'ℹ️ Info'),
    ('warning', '⚠️ Warning'),
    ('error', '❌ Error'),
    ('critical', '🔥 Critical'),
]

# ============================================================================
# TYPES DE NOTIFICATIONS
# ============================================================================
NOTIFICATION_TYPES = [
    ('email', '📧 Email'),
    ('slack', '💬 Slack'),
    ('webhook', '🔗 Webhook'),
    ('teams', '👥 Microsoft Teams'),
    ('sms', '📱 SMS'),
]

# ============================================================================
# COULEURS PAR TYPE DE PIPELINE
# ============================================================================
PIPELINE_COLORS = {
    'extract': '#28a745',
    'load': '#17a2b8',
    'etl': '#007bff',
    'elt': '#6f42c1',
    'replication': '#fd7e14',
    'migration': '#20c997',
    'aggregation': '#ffc107',
    'cleaning': '#dc3545',
}

# ============================================================================
# SEUILS PAR DÉFAUT
# ============================================================================
DEFAULT_THRESHOLDS = {
    'timeout_seconds': 3600,
    'retry_count': 3,
    'retry_delay_seconds': 60,
    'batch_size': 10000,
    'max_errors': 100,
    'memory_limit_mb': 1024,
}

# ============================================================================
# TYPES DE SOURCES/CIBLES
# ============================================================================
ENDPOINT_TYPES = [
    ('database', '🗄️ Database'),
    ('file', '📁 File'),
    ('api', '🌐 API'),
    ('message_queue', '📨 Message Queue'),
    ('data_warehouse', '🏢 Data Warehouse'),
    ('data_lake', '🌊 Data Lake'),
    ('streaming', '📡 Streaming'),
]

# ============================================================================
# TYPES DE DÉCLENCHEURS
# ============================================================================
TRIGGERED_BY_CHOICES = [
    ('manual', '👤 Manuel'),
    ('schedule', '⏰ Planification'),
    ('api', '🌐 API'),
    ('dependency', '🔗 Dépendance'),
    ('retry', '🔄 Réessai'),
    ('webhook', '🔌 Webhook'),
]