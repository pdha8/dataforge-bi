# apps/star_schema/enums.py
"""
Enums pour l'application star_schema
"""
from enum import Enum


class SchemaType(str, Enum):
    """Types de schémas"""
    STAR = 'star'
    SNOWFLAKE = 'snowflake'
    GALAXY = 'galaxy'
    CONSTELLATION = 'constellation'


class RelationType(str, Enum):
    """Types de relations"""
    ONE_TO_ONE = 'one_to_one'
    ONE_TO_MANY = 'one_to_many'
    MANY_TO_ONE = 'many_to_one'
    MANY_TO_MANY = 'many_to_many'


class JoinType(str, Enum):
    """Types de jointures"""
    INNER = 'inner'
    LEFT = 'left'
    RIGHT = 'right'
    FULL = 'full'
    CROSS = 'cross'


class GrainLevel(str, Enum):
    """Niveaux de grain"""
    TRANSACTION = 'transaction'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'


class FilterType(str, Enum):
    """Types de filtres"""
    EQUALS = 'equals'
    NOT_EQUALS = 'not_equals'
    GREATER_THAN = 'greater_than'
    LESS_THAN = 'less_than'
    BETWEEN = 'between'
    IN = 'in'
    LIKE = 'like'
    IS_NULL = 'is_null'
    IS_NOT_NULL = 'is_not_null'


class Status(str, Enum):
    """Statuts"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    DEPRECATED = 'deprecated'


class CalculationType(str, Enum):
    """Types de calcul"""
    DIRECT = 'direct'
    AGGREGATE = 'aggregate'
    RATIO = 'ratio'
    TREND = 'trend'
    FORECAST = 'forecast'
    CUMULATIVE = 'cumulative'
    MOVING_AVERAGE = 'moving_average'