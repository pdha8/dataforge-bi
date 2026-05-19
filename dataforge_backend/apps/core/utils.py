# apps/core/utils.py
"""
Utilitaires complets pour Sotifibre BI Platform
- Génération d'identifiants et tokens
- Formatage de données
- Manipulation de données BI
- Sécurité et validation
- Cache et performances
- Analyse et agrégations
"""
import uuid
import hashlib
import secrets
import string
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from decimal import Decimal
import re

from django.utils import timezone
from django.core.cache import cache
from django.utils.timesince import timesince

logger = logging.getLogger(__name__)


# ============================================================================
# GÉNÉRATION D'IDENTIFIANTS ET TOKENS
# ============================================================================

def generate_unique_id() -> str:
    """Génère un ID unique (UUID)"""
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Génère un token aléatoire sécurisé"""
    return secrets.token_urlsafe(length)


def generate_readable_code(length: int = 8) -> str:
    """Génère un code alphanumérique lisible (sans caractères ambigus)"""
    alphabet = string.ascii_uppercase + string.digits
    # Enlever les caractères ambigus
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_hash(string: str) -> str:
    """Génère un hash SHA256 d'une chaîne"""
    return hashlib.sha256(string.encode()).hexdigest()


def hash_file(file_obj) -> str:
    """Génère un hash MD5 d'un fichier"""
    hasher = hashlib.md5()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


# ============================================================================
# FORMATAGE DE DONNÉES
# ============================================================================

def format_bytes(size_bytes: int) -> str:
    """Formate une taille en bytes (humain lisible)"""
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.1f} {units[i]}"


def format_duration(seconds: float) -> str:
    """Formate une durée en secondes (humain lisible)"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def format_timesince(dt, default="maintenant") -> str:
    """Formate le temps écoulé depuis une date"""
    if not dt:
        return default
    return timesince(dt)


def format_number(value: Any, decimals: int = 2, compact: bool = False) -> str:
    """Formate un nombre avec unités K/M/B"""
    if value is None:
        return "N/A"
    
    try:
        num = float(value)
        
        if compact:
            if abs(num) >= 1_000_000_000:
                return f"{num / 1_000_000_000:.{decimals}f}B"
            elif abs(num) >= 1_000_000:
                return f"{num / 1_000_000:.{decimals}f}M"
            elif abs(num) >= 1_000:
                return f"{num / 1_000:.{decimals}f}K"
        
        # Formatage avec séparateurs de milliers
        if isinstance(value, (int, float)) and not compact:
            return f"{num:,.{decimals}f}".replace(",", " ")
        
        return f"{num:.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: float, decimals: int = 1, include_sign: bool = False) -> str:
    """Formate un pourcentage"""
    if value is None:
        return "N/A"
    
    sign = '+' if include_sign and value > 0 else ''
    return f"{sign}{value:.{decimals}f}%"


def format_currency(value: float, currency: str = '€', decimals: int = 2) -> str:
    """Formate une valeur monétaire"""
    if value is None:
        return "N/A"
    
    formatted = f"{value:,.{decimals}f}".replace(",", " ")
    return f"{formatted} {currency}"


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Tronque une chaîne à une longueur maximale"""
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# ============================================================================
# MANIPULATION DE DONNÉES
# ============================================================================

def parse_json_field(value: Any, default: Any = None) -> Union[Dict, List]:
    """Parse un champ JSON de manière sécurisée"""
    if not value:
        return default or {}
    
    if isinstance(value, (dict, list)):
        return value
    
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Aplatit un dictionnaire imbriqué"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{i}", sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Divise une liste en morceaux"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Division sécurisée (évite la division par zéro)"""
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_percentage_change(old_value: float, new_value: float) -> Optional[float]:
    """Calcule le changement en pourcentage entre deux valeurs"""
    if old_value == 0:
        return None
    return ((new_value - old_value) / abs(old_value)) * 100


def calculate_trend(current: float, previous: float) -> Dict[str, Any]:
    """
    Calcule la tendance entre deux valeurs
    """
    if previous == 0:
        change = 0 if current == 0 else 100
    else:
        change = ((current - previous) / previous) * 100
    
    direction = 'up' if change > 0 else 'down' if change < 0 else 'stable'
    icon = '📈' if change > 0 else '📉' if change < 0 else '➡️'
    
    return {
        'value': current,
        'previous': previous,
        'change': round(change, 1),
        'direction': direction,
        'icon': icon,
        'percentage': format_percentage(change, 1)
    }


def get_client_ip(request) -> str:
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================================
# PLAGES DE DATES
# ============================================================================

def get_date_range(period: str = 'day') -> Tuple[datetime, datetime]:
    """Retourne une plage de dates selon la période"""
    now = timezone.now()
    
    ranges = {
        'day': (now - timedelta(days=1), now),
        'week': (now - timedelta(weeks=1), now),
        'month': (now - timedelta(days=30), now),
        'quarter': (now - timedelta(days=90), now),
        'year': (now - timedelta(days=365), now),
        'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), now),
        'yesterday': (
            (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        'this_week': (
            (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            now
        ),
        'this_month': (
            now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            now
        ),
        'this_year': (
            now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            now
        ),
    }
    
    return ranges.get(period, ranges['day'])


def get_date_ranges() -> Dict[str, Tuple]:
    """Retourne les plages de dates communes"""
    now = timezone.now()
    today = now.date()
    
    return {
        'today': (today, today),
        'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
        'last_7_days': (today - timedelta(days=7), today),
        'last_30_days': (today - timedelta(days=30), today),
        'last_90_days': (today - timedelta(days=90), today),
        'this_month': (today.replace(day=1), today),
        'this_year': (today.replace(month=1, day=1), today),
        'last_year': (
            today.replace(year=today.year - 1, month=1, day=1),
            today.replace(year=today.year - 1, month=12, day=31)
        ),
    }


def parse_filter_params(query_params: Dict) -> Dict:
    """Parse les paramètres de filtre communs"""
    filters = {}
    
    # Date range
    date_from = query_params.get('date_from')
    date_to = query_params.get('date_to')
    if date_from:
        filters['created_at__date__gte'] = date_from
    if date_to:
        filters['created_at__date__lte'] = date_to
    
    # Preset ranges
    preset = query_params.get('date_range')
    if preset:
        ranges = get_date_ranges()
        if preset in ranges:
            start, end = ranges[preset]
            filters['created_at__date__gte'] = start
            filters['created_at__date__lte'] = end
    
    return filters


# ============================================================================
# CACHE ET PERFORMANCE
# ============================================================================

def build_cache_key(*args) -> str:
    """Construit une clé de cache cohérente"""
    parts = [str(a) for a in args if a is not None]
    return ':'.join(parts)


def rate_limit_check(key: str, max_calls: int, period_seconds: int) -> bool:
    """
    Limitation de taux simple avec Redis.
    Retourne True si dans les limites, False si dépassé.
    """
    cache_key = f"rate_limit:{key}"
    current = cache.get(cache_key, 0)
    
    if current >= max_calls:
        return False
    
    if current == 0:
        cache.set(cache_key, 1, period_seconds)
    else:
        cache.incr(cache_key)
    
    return True


class Timer:
    """Timer simple pour le monitoring des performances"""
    
    def __init__(self, name: str = 'operation'):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed = 0
    
    def start(self):
        """Démarre le timer"""
        self.start_time = timezone.now()
        return self
    
    def stop(self):
        """Arrête le timer"""
        self.end_time = timezone.now()
        if self.start_time:
            self.elapsed = (self.end_time - self.start_time).total_seconds() * 1000
        return self
    
    def duration(self) -> Optional[float]:
        """Retourne la durée en secondes"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def duration_ms(self) -> Optional[float]:
        """Retourne la durée en millisecondes"""
        seconds = self.duration()
        return seconds * 1000 if seconds else None
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, *args):
        """Context manager exit"""
        self.stop()
        if self.elapsed > 1000:  # Plus d'1 seconde
            logger.debug(f"{self.name} took {self.elapsed:.2f}ms")


# ============================================================================
# ANALYSE DE DONNÉES BI
# ============================================================================

def aggregate_data(df, group_by: List[str], aggregations: Dict[str, str]):
    """
    Agrège des données selon des critères
    Nécessite pandas
    """
    try:
        import pandas as pd
        return df.groupby(group_by).agg(aggregations).reset_index()
    except ImportError:
        logger.warning("pandas not installed")
        return df


def pivot_data(df, index: List[str], columns: str, values: str, aggfunc: str = 'sum'):
    """
    Pivote des données
    Nécessite pandas
    """
    try:
        import pandas as pd
        return df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc).reset_index()
    except ImportError:
        logger.warning("pandas not installed")
        return df


def detect_data_type(series) -> str:
    """
    Détecte le type de données d'une colonne
    Nécessite pandas
    """
    try:
        import pandas as pd
        if pd.api.types.is_numeric_dtype(series):
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        elif pd.api.types.is_categorical_dtype(series):
            return 'categorical'
        elif pd.api.types.is_bool_dtype(series):
            return 'boolean'
        else:
            return 'text'
    except ImportError:
        return 'unknown'


def get_color_palette(theme: str = 'default') -> List[str]:
    """
    Retourne une palette de couleurs pour les graphiques
    """
    palettes = {
        'default': ['#5470c6', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'],
        'dark': ['#2d8cff', '#36cbcb', '#f9d857', '#ff8c6e', '#b57cff', '#ff6b6b', '#4cd964', '#ff9500'],
        'pastel': ['#88b0dc', '#f5b7b2', '#a2d4c9', '#f9d6b0', '#c7b8ea', '#f5a97f', '#b8e1fc', '#f5b7b2'],
        'corporate': ['#003f5c', '#2c4c6e', '#58508d', '#bc5090', '#ff6361', '#ffa600', '#7c4dff', '#00c853'],
        'blue': ['#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#e6550d', '#fd8d3c', '#fdae6b', '#fdd0a2'],
        'green': ['#31a354', '#74c476', '#a1d99b', '#c7e9c0', '#756bb1', '#9e9ac8', '#cbc9e2', '#dadaeb'],
    }
    
    return palettes.get(theme, palettes['default'])


def get_chart_config(chart_type: str, data: Dict, options: Dict = None) -> Dict:
    """
    Génère la configuration pour un graphique
    """
    options = options or {}
    
    base_config = {
        'title': {'text': options.get('title', ''), 'left': 'center'},
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'legend': {'show': options.get('legend', True), 'orient': 'vertical', 'left': 'left'},
        'grid': {'containLabel': True, 'left': '3%', 'right': '4%', 'bottom': '3%'},
    }
    
    if chart_type == 'bar':
        config = {
            **base_config,
            'xAxis': {'type': 'category', 'data': data.get('categories', [])},
            'yAxis': {'type': 'value'},
            'series': [{
                'name': s.get('name', ''),
                'type': 'bar',
                'data': s.get('data', []),
                'itemStyle': {'borderRadius': [4, 4, 0, 0]}
            } for s in data.get('series', [])],
        }
    
    elif chart_type == 'line':
        config = {
            **base_config,
            'xAxis': {'type': 'category', 'data': data.get('categories', [])},
            'yAxis': {'type': 'value'},
            'series': [{
                'name': s.get('name', ''),
                'type': 'line',
                'data': s.get('data', []),
                'smooth': options.get('smooth', True),
                'areaStyle': options.get('area', False) and {}
            } for s in data.get('series', [])],
        }
    
    elif chart_type == 'pie':
        config = {
            **base_config,
            'tooltip': {'trigger': 'item'},
            'series': [{
                'name': options.get('series_name', ''),
                'type': 'pie',
                'radius': options.get('radius', '55%'),
                'center': options.get('center', ['50%', '50%']),
                'data': data.get('data', []),
                'emphasis': {'scale': True},
                'label': {'show': options.get('labels', True)}
            }],
        }
    
    elif chart_type == 'heatmap':
        config = {
            **base_config,
            'xAxis': {'type': 'category', 'data': data.get('x_categories', []), 'splitArea': {'show': True}},
            'yAxis': {'type': 'category', 'data': data.get('y_categories', []), 'splitArea': {'show': True}},
            'visualMap': {
                'min': data.get('min', 0),
                'max': data.get('max', 100),
                'calculable': True,
                'orient': 'horizontal',
                'left': 'center',
                'bottom': '0%'
            },
            'series': [{
                'name': options.get('series_name', ''),
                'type': 'heatmap',
                'data': data.get('data', []),
                'label': {'show': False},
                'emphasis': {'scale': True}
            }],
        }
    
    elif chart_type == 'gauge':
        config = {
            **base_config,
            'tooltip': {'trigger': 'item'},
            'series': [{
                'name': options.get('series_name', ''),
                'type': 'gauge',
                'progress': {'show': True},
                'detail': {'valueAnimation': True, 'fontSize': 30},
                'data': [{'value': data.get('value', 0), 'name': data.get('name', '')}],
                'axisLabel': {'fontSize': 12},
                'title': {'fontSize': 14}
            }],
        }
    
    else:
        config = base_config
    
    return config


def calculate_statistics(data: List[Dict], field: str) -> Dict[str, Any]:
    """
    Calcule des statistiques sur une liste de données
    """
    if not data:
        return {'count': 0, 'sum': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    values = [float(item.get(field, 0)) for item in data if item.get(field) is not None]
    
    if not values:
        return {'count': 0, 'sum': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    return {
        'count': len(values),
        'sum': sum(values),
        'avg': sum(values) / len(values),
        'min': min(values),
        'max': max(values),
        'median': sorted(values)[len(values) // 2],
    }


def safe_eval_expression(expression: str, context: Dict = None) -> Any:
    """
    Évalue une expression de manière sécurisée (pour les formules BI)
    """
    import ast
    import operator as op
    
    # Opérateurs autorisés
    operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
        ast.USub: op.neg,
    }
    
    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Name):
            if context and node.id in context:
                return context[node.id]
            raise NameError(f"Variable non définie: {node.id}")
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Type non supporté: {type(node)}")
    
    try:
        tree = ast.parse(expression, mode='eval')
        return _eval(tree.body)
    except Exception as e:
        logger.error(f"Erreur évaluation expression: {e}")
        return None


# ============================================================================
# VALIDATION ET SÉCURITÉ
# ============================================================================

def validate_email(email: str) -> bool:
    """Valide une adresse email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_sql_query_safe(query: str) -> bool:
    """
    Valide une requête SQL (vérification de sécurité)
    """
    import sqlparse
    
    if not query:
        return False
    
    try:
        parsed = sqlparse.parse(query)
        if not parsed:
            return False
        
        query_upper = query.upper()
        
        # Mots-clés dangereux
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                logger.warning(f"Requête SQL contient mot-clé dangereux: {keyword}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Erreur validation SQL: {e}")
        return False