# apps/core/constants.py
"""
Constantes globales pour la plateforme Sotifibre BI
"""

# Méthodes HTTP
HTTP_METHODS = {
    'GET': 'GET',
    'POST': 'POST',
    'PUT': 'PUT',
    'PATCH': 'PATCH',
    'DELETE': 'DELETE',
    'OPTIONS': 'OPTIONS',
    'HEAD': 'HEAD',
}

# Méthodes sûres (lecture seule)
SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

# Informations de la plateforme
PLATFORM = {
    'name': 'Sotifibre',
    'version': '1.0.0',
    'description': 'Plateforme Business Intelligence Avancée',
    'website': 'https://sotifibre.io',
    'company': 'Sotifibre Analytics',
    'support_email': 'support@sotifibre.io',
}

# Pagination par défaut
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Durées de cache (secondes)
CACHE_TTL = {
    'short': 60,           # 1 minute
    'medium': 300,         # 5 minutes
    'long': 3600,          # 1 heure
    'day': 86400,          # 1 jour
    'week': 604800,        # 1 semaine
    'month': 2592000,      # 30 jours
}

# Niveaux de qualité des données
DATA_QUALITY = {
    'excellent': '⭐ Excellent',
    'good': '✅ Bon',
    'warning': '⚠️ Attention',
    'poor': '🔴 Médiocre',
    'unknown': '❓ Inconnu',
}

# Statuts des pipelines ETL
ETL_STATUS = {
    'pending': '⏳ En attente',
    'running': '🔄 En cours',
    'completed': '✅ Terminé',
    'failed': '❌ Échoué',
    'cancelled': '🚫 Annulé',
    'scheduled': '📅 Planifié',
}

# Types d'agrégations
AGGREGATION_TYPES = {
    'sum': '➕ Somme',
    'avg': '📊 Moyenne',
    'count': '🔢 Comptage',
    'min': '⬇️ Minimum',
    'max': '⬆️ Maximum',
    'median': '📈 Médiane',
    'std': '📉 Écart-type',
    'variance': '📊 Variance',
}

# Types de graphiques
CHART_TYPES = {
    'bar': '📊 Barres',
    'line': '📈 Ligne',
    'pie': '🥧 Camembert',
    'area': '📉 Aire',
    'scatter': '🔵 Nuage de points',
    'heatmap': '🔥 Heatmap',
    'funnel': '🔻 Entonnoir',
    'gauge': '🎯 Jauge',
    'map': '🗺️ Carte',
    'table': '📋 Tableau',
    'pivot': '🔄 Tableau croisé',
}

# Formats de visualisation
VISUALIZATION_FORMATS = {
    'echarts': 'ECharts',
    'chartjs': 'Chart.js',
    'plotly': 'Plotly',
    'highcharts': 'Highcharts',
    'd3': 'D3.js',
}

# Types de sources de données
DATA_SOURCE_TYPES = {
    'database': '🗄️ Base de données',
    'api': '🌐 API',
    'file': '📁 Fichier',
    'cloud': '☁️ Cloud',
    'streaming': '📡 Streaming',
    'data_warehouse': '🏢 Data Warehouse',
    'data_lake': '🌊 Data Lake',
}

# Types de bases de données
DATABASE_TYPES = {
    'postgresql': '🐘 PostgreSQL',
    'mysql': '🐬 MySQL',
    'sqlserver': '🔷 SQL Server',
    'oracle': '🔶 Oracle',
    'mongodb': '🍃 MongoDB',
    'redis': '📀 Redis',
    'clickhouse': '🏠 ClickHouse',
    'snowflake': '❄️ Snowflake',
    'bigquery': '☁️ BigQuery',
    'redshift': '🔴 Redshift',
}

# Types de fichiers
FILE_TYPES = {
    'csv': '📊 CSV',
    'excel': '📈 Excel',
    'json': '🔧 JSON',
    'parquet': '📦 Parquet',
    'avro': '📀 Avro',
    'orc': '🎯 ORC',
    'xml': '📄 XML',
}

# Fréquences de rafraîchissement
REFRESH_FREQUENCIES = {
    'realtime': '⚡ Temps réel',
    'minute': '⏱️ Toutes les minutes',
    '5min': '🕐 5 minutes',
    '15min': '🕒 15 minutes',
    'hourly': '🕓 Horaire',
    'daily': '📅 Quotidien',
    'weekly': '📆 Hebdomadaire',
    'monthly': '🗓️ Mensuel',
    'quarterly': '📊 Trimestriel',
    'yearly': '📈 Annuel',
}

# Types de calculs
CALCULATION_TYPES = {
    'direct': '🎯 Direct',
    'aggregate': '📊 Agrégation',
    'ratio': '📐 Ratio',
    'trend': '📈 Tendance',
    'forecast': '🔮 Prédiction',
    'cumulative': '📊 Cumul',
    'moving_average': '📉 Moyenne mobile',
}

# Niveaux d'accès
ACCESS_LEVELS = {
    'owner': '👑 Propriétaire',
    'editor': '✏️ Éditeur',
    'viewer': '👀 Observateur',
    'commenter': '💬 Commentateur',
}

# Types de permissions
PERMISSION_TYPES = {
    'view': '👁️ Voir',
    'edit': '✏️ Modifier',
    'delete': '🗑️ Supprimer',
    'share': '🔗 Partager',
    'export': '📤 Exporter',
    'schedule': '📅 Planifier',
    'admin': '⚙️ Administrer',
}

# Statuts des tableaux de bord
DASHBOARD_STATUS = {
    'draft': '📝 Brouillon',
    'published': '✅ Publié',
    'archived': '📦 Archivé',
    'deleted': '🗑️ Supprimé',
}

# Rôles utilisateur BI
BI_USER_ROLES = {
    'admin': '👑 Administrateur BI',
    'analyst': '📊 Analyste',
    'developer': '💻 Développeur',
    'viewer': '👀 Observateur',
    'consumer': '📱 Consommateur',
}