# apps/star_schema/constants.py
"""
Constantes pour l'application star_schema
"""

# ============================================================================
# TYPES DE SCHÉMAS
# ============================================================================
SCHEMA_TYPES = [
    ('star', '⭐ Schéma en étoile'),
    ('snowflake', '❄️ Schéma en flocon'),
    ('galaxy', '🌌 Schéma galaxie'),
    ('constellation', '✨ Constellation de faits'),
]

# ============================================================================
# TYPES DE RELATIONS
# ============================================================================
RELATION_TYPES = [
    ('one_to_one', '1:1 - Un à un'),
    ('one_to_many', '1:N - Un à plusieurs'),
    ('many_to_one', 'N:1 - Plusieurs à un'),
    ('many_to_many', 'N:N - Plusieurs à plusieurs'),
]

# ============================================================================
# TYPES DE JOINTURES
# ============================================================================
JOIN_TYPES = [
    ('inner', '🔗 INNER JOIN'),
    ('left', '⬅️ LEFT JOIN'),
    ('right', '➡️ RIGHT JOIN'),
    ('full', '🔄 FULL OUTER JOIN'),
    ('cross', '✖️ CROSS JOIN'),
]

# ============================================================================
# NIVEAUX DE GRAIN
# ============================================================================
GRAIN_LEVELS = [
    ('transaction', '📝 Transaction'),
    ('daily', '📅 Quotidien'),
    ('weekly', '📆 Hebdomadaire'),
    ('monthly', '🗓️ Mensuel'),
    ('quarterly', '📊 Trimestriel'),
    ('yearly', '📈 Annuel'),
]

# ============================================================================
# TYPES DE FILTRES
# ============================================================================
FILTER_TYPES = [
    ('equals', '= Égal à'),
    ('not_equals', '≠ Différent de'),
    ('greater_than', '> Supérieur à'),
    ('less_than', '< Inférieur à'),
    ('greater_or_equal', '≥ Supérieur ou égal'),
    ('less_or_equal', '≤ Inférieur ou égal'),
    ('between', '📊 Entre'),
    ('in', '📋 Dans la liste'),
    ('like', '🔍 Contient'),
    ('is_null', '❓ Est NULL'),
    ('is_not_null', '✅ N\'est pas NULL'),
]

# ============================================================================
# STATUTS
# ============================================================================
STATUS_CHOICES = [
    ('draft', '📝 Brouillon'),
    ('active', '✅ Actif'),
    ('archived', '📦 Archivé'),
    ('deprecated', '⚠️ Obsolète'),
]

# ============================================================================
# TYPES DE CALCUL
# ============================================================================
CALCULATION_TYPES = [  # ✅ Ajouté pour corriger l'erreur
    ('direct', '🎯 Direct'),
    ('aggregate', '📊 Agrégation'),
    ('ratio', '📐 Ratio'),
    ('trend', '📈 Tendance'),
    ('forecast', '🔮 Prédiction'),
    ('cumulative', '📊 Cumul'),
    ('moving_average', '📉 Moyenne mobile'),
    ('year_over_year', '📈 Variation annuelle'),
    ('month_over_month', '📊 Variation mensuelle'),
    ('percentage', '📊 Pourcentage'),
]