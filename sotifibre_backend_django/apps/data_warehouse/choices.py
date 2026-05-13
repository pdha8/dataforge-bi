# apps/data_warehouse/choices.py
"""
Choix pour l'application data_warehouse
"""
from .constants import (
    TABLE_TYPES,
    DIMENSION_TYPES,
    SCD_TYPES,
    GRANULARITIES,
    AGGREGATION_TYPES,
    PARTITION_TYPES,
    TABLE_STATUS,
    REFRESH_FREQUENCIES,
    COLUMN_TYPES,
)

__all__ = [
    'TABLE_TYPES',
    'DIMENSION_TYPES',
    'SCD_TYPES',
    'GRANULARITIES',
    'AGGREGATION_TYPES',
    'PARTITION_TYPES',
    'TABLE_STATUS',
    'REFRESH_FREQUENCIES',
    'COLUMN_TYPES',
]