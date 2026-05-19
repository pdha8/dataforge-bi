# apps/etl_engine/enums.py
"""
Enums pour l'application etl_engine
"""
from enum import Enum


class PipelineType(str, Enum):
    """Types de pipelines"""
    EXTRACT = 'extract'
    LOAD = 'load'
    ETL = 'etl'
    ELT = 'elt'
    REPLICATION = 'replication'
    MIGRATION = 'migration'
    AGGREGATION = 'aggregation'
    CLEANING = 'cleaning'


class PipelineStatus(str, Enum):
    """Statuts des pipelines"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    PAUSED = 'paused'
    ERROR = 'error'
    ARCHIVED = 'archived'
    DEPRECATED = 'deprecated'


class ExecutionStatus(str, Enum):
    """Statuts des exécutions"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    SKIPPED = 'skipped'
    RETRYING = 'retrying'


class TransformationType(str, Enum):
    """Types de transformations"""
    FILTER = 'filter'
    SELECT = 'select'
    RENAME = 'rename'
    CAST = 'cast'
    AGGREGATE = 'aggregate'
    JOIN = 'join'
    UNION = 'union'
    SORT = 'sort'
    GROUP_BY = 'group_by'
    PIVOT = 'pivot'
    UNPIVOT = 'unpivot'
    WINDOW = 'window'
    CUSTOM_SQL = 'custom_sql'
    CUSTOM_PYTHON = 'custom_python'
    VALIDATION = 'validation'
    DEDUPLICATE = 'deduplicate'
    FILLNA = 'fillna'
    DROPNA = 'dropna'
    NORMALIZE = 'normalize'
    ENCODE = 'encode'
    SPLIT = 'split'
    MERGE = 'merge'


class ErrorStrategy(str, Enum):
    """Stratégies de gestion des erreurs"""
    FAIL = 'fail'
    SKIP = 'skip'
    DEFAULT = 'default'
    RETRY = 'retry'
    NOTIFY = 'notify'
    CONTINUE = 'continue'


class ProcessingMode(str, Enum):
    """Modes de traitement"""
    BATCH = 'batch'
    STREAMING = 'streaming'
    INCREMENTAL = 'incremental'
    FULL = 'full'


class LogLevel(str, Enum):
    """Niveaux de log"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'