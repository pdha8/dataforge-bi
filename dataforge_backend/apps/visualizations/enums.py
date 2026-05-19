# apps/visualizations/enums.py
"""
Enums pour l'application visualizations
"""
from enum import Enum


class ChartType(str, Enum):
    """Types de graphiques"""
    BAR = 'bar'
    LINE = 'line'
    PIE = 'pie'
    AREA = 'area'
    SCATTER = 'scatter'
    HEATMAP = 'heatmap'
    FUNNEL = 'funnel'
    GAUGE = 'gauge'
    MAP = 'map'
    TABLE = 'table'
    PIVOT = 'pivot'
    RADAR = 'radar'
    TREEMAP = 'treemap'
    SANKEY = 'sankey'
    SUNBURST = 'sunburst'
    WATERFALL = 'waterfall'
    BOX = 'box'
    HISTOGRAM = 'histogram'


class DashboardType(str, Enum):
    """Types de tableaux de bord"""
    ANALYTICAL = 'analytical'
    OPERATIONAL = 'operational'
    EXECUTIVE = 'executive'
    STRATEGIC = 'strategic'
    TACTICAL = 'tactical'
    CUSTOM = 'custom'


class RefreshFrequency(str, Enum):
    """Fréquences de rafraîchissement"""
    REALTIME = 'realtime'
    SECOND = 'second'
    MINUTE = 'minute'
    FIVE_MINUTES = '5min'
    FIFTEEN_MINUTES = '15min'
    THIRTY_MINUTES = '30min'
    HOURLY = 'hourly'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    MANUAL = 'manual'


class ExportFormat(str, Enum):
    """Formats d'export"""
    PNG = 'png'
    SVG = 'svg'
    PDF = 'pdf'
    CSV = 'csv'
    EXCEL = 'excel'
    JSON = 'json'
    HTML = 'html'
    MARKDOWN = 'markdown'


class Status(str, Enum):
    """Statuts"""
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    DELETED = 'deleted'
    SCHEDULED = 'scheduled'


class AccessLevel(str, Enum):
    """Niveaux d'accès"""
    PRIVATE = 'private'
    TEAM = 'team'
    ORGANIZATION = 'organization'
    PUBLIC = 'public'
    PUBLIC_EDIT = 'public_edit'


class WidgetType(str, Enum):
    """Types de widgets"""
    CHART = 'chart'
    METRIC = 'metric'
    TABLE = 'table'
    TEXT = 'text'
    IMAGE = 'image'
    IFRAME = 'iframe'
    CUSTOM = 'custom'


class KPIType(str, Enum):
    """Types de KPI"""
    NUMBER = 'number'
    PERCENTAGE = 'percentage'
    CURRENCY = 'currency'
    RATIO = 'ratio'
    TREND = 'trend'
    COMPARISON = 'comparison'


class TrendDirection(str, Enum):
    """Directions de tendance"""
    UP = 'up'
    DOWN = 'down'
    STABLE = 'stable'
    VOLATILE = 'volatile'