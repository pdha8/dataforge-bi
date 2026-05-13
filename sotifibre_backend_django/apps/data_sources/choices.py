# apps/data_sources/choices.py
"""
Choix pour les modèles de l'application data_sources - Version optimisée
"""
from .constants import (
    SOURCE_TYPE_CHOICES,
    STATUS_CHOICES,
    REFRESH_CHOICES,
    FILE_PROCESS_STATUS,
    LOG_LEVEL_CHOICES,
    QUERY_STEP_TYPES,
    DATABASE_TYPES,
    API_TYPES,
    FILE_TYPES,
    AUTH_TYPES,
    CONNECTION_STATUS,
    SYNC_FREQUENCIES,
    QUERY_TYPES,
)

# Alias pour compatibilité
SOURCE_TYPES = SOURCE_TYPE_CHOICES
DATA_SOURCE_TYPES = SOURCE_TYPE_CHOICES

# Réexporter pour compatibilité
__all__ = [
    'SOURCE_TYPE_CHOICES',
    'SOURCE_TYPES',
    'DATA_SOURCE_TYPES',
    'STATUS_CHOICES',
    'REFRESH_CHOICES',
    'FILE_PROCESS_STATUS',
    'LOG_LEVEL_CHOICES',
    'QUERY_STEP_TYPES',
    'DATABASE_TYPES',
    'API_TYPES',
    'FILE_TYPES',
    'AUTH_TYPES',
    'CONNECTION_STATUS',
    'SYNC_FREQUENCIES',
    'QUERY_TYPES',
]