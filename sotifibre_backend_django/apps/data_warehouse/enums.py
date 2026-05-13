# apps/data_warehouse/enums.py
"""
Enums pour l'application data_warehouse
"""
from enum import Enum


class TableType(str, Enum):
    """Types de tables"""
    FACT = 'fact'
    DIMENSION = 'dimension'
    AGGREGATE = 'aggregate'
    BRIDGE = 'bridge'
    STAGING = 'staging'


class DimensionType(str, Enum):
    """Types de dimensions"""
    CONFORMED = 'conformed'
    DEGENERATE = 'degenerate'
    JUNK = 'junk'
    ROLE_PLAYING = 'role_playing'
    SLOWLY_CHANGING = 'slowly_changing'
    RAPIDLY_CHANGING = 'rapidly_changing'


class SCDType(str, Enum):
    """Types SCD"""
    TYPE0 = 'type0'
    TYPE1 = 'type1'
    TYPE2 = 'type2'
    TYPE3 = 'type3'
    TYPE4 = 'type4'
    TYPE6 = 'type6'


class Granularity(str, Enum):
    """Granularités"""
    TRANSACTION = 'transaction'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'


class AggregationType(str, Enum):
    """Types d'agrégation"""
    SUM = 'sum'
    AVG = 'avg'
    COUNT = 'count'
    MIN = 'min'
    MAX = 'max'
    COUNT_DISTINCT = 'count_distinct'
    STDDEV = 'stddev'
    VARIANCE = 'variance'