# apps/data_warehouse/constants.py
"""
Constantes pour l'application data_warehouse
"""

# ============================================================================
# TYPES DE TABLES
# ============================================================================
TABLE_TYPES = [
    ('fact', '📊 Table des faits'),
    ('dimension', '📐 Table de dimension'),
    ('aggregate', '📈 Table agrégée'),
    ('bridge', '🌉 Table de pont'),
    ('staging', '📥 Table de staging'),
]

# ============================================================================
# TYPES DE DIMENSIONS
# ============================================================================
DIMENSION_TYPES = [
    ('conformed', '✅ Conforme'),
    ('degenerate', '📊 Dégénérée'),
    ('junk', '🗑️ Junk'),
    ('role_playing', '🎭 Rôle multiple'),
    ('slowly_changing', '🐢 Évolution lente (SCD)'),
    ('rapidly_changing', '⚡ Évolution rapide'),
]

# ============================================================================
# TYPES SCD (Slowly Changing Dimension)
# ============================================================================
SCD_TYPES = [
    ('type0', '📝 Type 0 - Fixe'),
    ('type1', '🔄 Type 1 - Écrasement'),
    ('type2', '📅 Type 2 - Versionnage'),
    ('type3', '📊 Type 3 - Colonne d\'historique'),
    ('type4', '📁 Type 4 - Table d\'historique'),
    ('type6', '🔀 Type 6 - Hybride'),
]

# ============================================================================
# GRANULARITÉS
# ============================================================================
GRANULARITIES = [
    ('transaction', '📝 Transaction'),
    ('daily', '📅 Quotidienne'),
    ('weekly', '📆 Hebdomadaire'),
    ('monthly', '🗓️ Mensuelle'),
    ('quarterly', '📊 Trimestrielle'),
    ('yearly', '📈 Annuelle'),
]

# ============================================================================
# TYPES D'AGRÉGATION
# ============================================================================
AGGREGATION_TYPES = [
    ('sum', '➕ Somme'),
    ('avg', '📊 Moyenne'),
    ('count', '🔢 Comptage'),
    ('min', '⬇️ Minimum'),
    ('max', '⬆️ Maximum'),
    ('count_distinct', '🔢 Comptage distinct'),
    ('median', '📈 Médiane'),
    ('std', '📉 Écart-type'),
    ('variance', '📊 Variance'),
    ('percentile_25', '📊 25ème percentile'),
    ('percentile_75', '📊 75ème percentile'),
    ('percentile_90', '📊 90ème percentile'),
    ('percentile_95', '📊 95ème percentile'),
    ('percentile_99', '📊 99ème percentile'),
]

# ============================================================================
# STRATÉGIES DE PARTITIONNEMENT
# ============================================================================
PARTITION_TYPES = [
    ('range', '📊 Range'),
    ('list', '📋 List'),
    ('hash', '#️⃣ Hash'),
]

# ============================================================================
# STATUTS DES TABLES
# ============================================================================
TABLE_STATUS = [
    ('active', '✅ Actif'),
    ('building', '🏗️ En construction'),
    ('deprecated', '⚠️ Obsolète'),
    ('archived', '📦 Archivé'),
]

# ============================================================================
# FRÉQUENCES DE RAFRAÎCHISSEMENT
# ============================================================================
REFRESH_FREQUENCIES = [
    ('realtime', '⚡ Temps réel'),
    ('hourly', '🕓 Horaire'),
    ('daily', '📅 Quotidien'),
    ('weekly', '📆 Hebdomadaire'),
    ('monthly', '🗓️ Mensuel'),
    ('manual', '👤 Manuel'),
]

# ============================================================================
# TYPES DE COLONNES
# ============================================================================
COLUMN_TYPES = [
    ('integer', '🔢 Entier'),
    ('bigint', '📊 Grand entier'),
    ('decimal', '💵 Décimal'),
    ('float', '📈 Float'),
    ('date', '📅 Date'),
    ('datetime', '⏰ Date/heure'),
    ('timestamp', '🕐 Timestamp'),
    ('boolean', '✅ Booléen'),
    ('varchar', '📝 Texte'),
    ('text', '📄 Texte long'),
    ('json', '🔧 JSON'),
    ('uuid', '🆔 UUID'),
]