# apps/visualizations/constants.py
"""
Constantes pour l'application visualizations
"""

# ============================================================================
# TYPES DE GRAPHIQUES AVANCÉS
# ============================================================================
CHART_TYPES = [
    ('bar', '📊 Barres'),
    ('line', '📈 Ligne'),
    ('pie', '🥧 Camembert'),
    ('area', '📉 Aire'),
    ('scatter', '🔵 Nuage de points'),
    ('heatmap', '🔥 Heatmap'),
    ('funnel', '🔻 Entonnoir'),
    ('gauge', '🎯 Jauge'),
    ('map', '🗺️ Carte'),
    ('table', '📋 Tableau'),
    ('pivot', '🔄 Tableau croisé'),
    ('radar', '🕸️ Radar'),
    ('treemap', '🌳 Treemap'),
    ('sankey', '🌊 Sankey'),
    ('sunburst', '☀️ Sunburst'),
    ('waterfall', '💧 Waterfall'),
    ('box', '📦 Boîte à moustaches'),
    ('histogram', '📊 Histogramme'),
    ('violin', '🎻 Violon'),
    ('candlestick', '🕯️ Chandelier'),
]

# ============================================================================
# TYPES DE DASHBOARDS
# ============================================================================
DASHBOARD_TYPES = [
    ('analytical', '📊 Analytique'),
    ('operational', '⚙️ Opérationnel'),
    ('executive', '👔 Exécutif'),
    ('strategic', '🎯 Stratégique'),
    ('tactical', '⚡ Tactique'),
    ('custom', '🎨 Personnalisé'),
]

# ============================================================================
# FRÉQUENCES DE RAFRAÎCHISSEMENT
# ============================================================================
REFRESH_FREQUENCIES = [
    ('realtime', '⚡ Temps réel (WebSocket)'),
    ('second', '⏱️ Chaque seconde'),
    ('minute', '🕐 Minute'),
    ('5min', '🕐 5 minutes'),
    ('15min', '🕒 15 minutes'),
    ('30min', '🕜 30 minutes'),
    ('hourly', '🕓 Horaire'),
    ('daily', '📅 Quotidien'),
    ('weekly', '📆 Hebdomadaire'),
    ('monthly', '🗓️ Mensuel'),
    ('manual', '👤 Manuel'),
]

# ============================================================================
# FORMATS D'EXPORT
# ============================================================================
EXPORT_FORMATS = [
    ('png', '🖼️ PNG (Image)'),
    ('svg', '📐 SVG (Vectoriel)'),
    ('pdf', '📄 PDF (Document)'),
    ('csv', '📊 CSV (Tableur)'),
    ('excel', '📈 Excel (XLSX)'),
    ('json', '🔧 JSON (API)'),
    ('html', '🌐 HTML (Web)'),
    ('markdown', '📝 Markdown'),
]

# ============================================================================
# THÈMES DE VISUALISATION
# ============================================================================
THEMES = [
    ('light', '☀️ Light'),
    ('dark', '🌙 Dark'),
    ('corporate', '🏢 Corporate'),
    ('scientific', '🔬 Scientific'),
    ('vibrant', '🌈 Vibrant'),
    ('pastel', '🎨 Pastel'),
    ('monochrome', '⚫ Monochrome'),
]

# ============================================================================
# STATUTS
# ============================================================================
STATUS_CHOICES = [
    ('draft', '📝 Brouillon'),
    ('published', '✅ Publié'),
    ('archived', '📦 Archivé'),
    ('deleted', '🗑️ Supprimé'),
    ('scheduled', '📅 Programmé'),
]

# ============================================================================
# NIVEAUX D'ACCÈS
# ============================================================================
ACCESS_LEVELS = [
    ('private', '🔒 Privé (Seul moi)'),
    ('team', '👥 Équipe'),
    ('organization', '🏢 Organisation'),
    ('public', '🌍 Public (Lecture seule)'),
    ('public_edit', '🌍 Public (Modifiable)'),
]

# ============================================================================
# TYPES DE WIDGETS
# ============================================================================
WIDGET_TYPES = [
    ('chart', '📊 Graphique'),
    ('metric', '📈 Métrique KPI'),
    ('table', '📋 Tableau'),
    ('text', '📝 Texte'),
    ('image', '🖼️ Image'),
    ('iframe', '🔗 Iframe'),
    ('custom', '⚙️ Personnalisé'),
]

# ============================================================================
# TYPES DE MÉTRIQUES KPI
# ============================================================================
KPI_TYPES = [
    ('number', '🔢 Nombre'),
    ('percentage', '📊 Pourcentage'),
    ('currency', '💰 Devise'),
    ('ratio', '📐 Ratio'),
    ('trend', '📈 Tendance'),
    ('comparison', '⚖️ Comparaison'),
]

# ============================================================================
# TENDANCES
# ============================================================================
TREND_DIRECTIONS = [
    ('up', '📈 Hausse'),
    ('down', '📉 Baisse'),
    ('stable', '➡️ Stable'),
    ('volatile', '🌊 Volatile'),
]