# apps/data_sources/validators.py
"""
Validateurs personnalisés pour les modèles data_sources - Version optimisée
"""
import re
import json
import sqlparse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import DANGEROUS_SQL_KEYWORDS, DEFAULT_PORTS


def validate_connection_string(value):
    """
    Valide une chaîne de connexion à une base de données
    """
    if not value:
        return value
    
    patterns = {
        'postgresql': r'^postgresql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'mysql': r'^mysql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'mongodb': r'^mongodb://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'sqlite': r'^sqlite:///(.+)$',
        'clickhouse': r'^clickhouse://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'snowflake': r'^snowflake://([^:]+):([^@]+)@([^/]+)/(.+)$',
        'bigquery': r'^bigquery://([^/]+)/([^?]+)',
        'redshift': r'^redshift://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'oracle': r'^oracle://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'sqlserver': r'^sqlserver://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
    }
    
    valid = False
    matched_type = None
    for name, pattern in patterns.items():
        if re.match(pattern, value):
            valid = True
            matched_type = name
            break
    
    if not valid:
        raise ValidationError(
            _('Format de connexion invalide. Utilisez: protocol://user:pass@host:port/database'),
            code='invalid_connection_string'
        )
    
    return value


def validate_hostname(value):
    """
    Valide un nom d'hôte ou une adresse IP
    """
    if not value:
        return value
    
    # IPv4
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # IPv6
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    # Hostname
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not (re.match(ipv4_pattern, value) or re.match(ipv6_pattern, value) or re.match(hostname_pattern, value)):
        raise ValidationError(_('Nom d\'hôte ou adresse IP invalide'), code='invalid_hostname')
    
    return value


def validate_port(value):
    """
    Valide un numéro de port
    """
    if value is None:
        return value
    
    if not (1 <= value <= 65535):
        raise ValidationError(_('Le port doit être compris entre 1 et 65535'), code='invalid_port')
    
    return value


def validate_sql_query(value):
    """
    Valide une requête SQL avec vérification de sécurité
    """
    if not value:
        return value
    
    value = value.strip()
    
    try:
        parsed = sqlparse.parse(value)
        if not parsed:
            raise ValidationError(_('Requête SQL vide'), code='empty_query')
        
        query_upper = value.upper()
        
        for keyword in DANGEROUS_SQL_KEYWORDS:
            if keyword in query_upper:
                raise ValidationError(
                    _(f'La requête contient le mot-clé interdit: {keyword}'),
                    code='dangerous_query'
                )
        
        statements = [s for s in value.split(';') if s.strip()]
        if len(statements) > 1:
            raise ValidationError(
                _('Les requêtes multiples ne sont pas autorisées'),
                code='multiple_statements'
            )
        
        first_statement = sqlparse.parse(statements[0])[0]
        first_token = next((t for t in first_statement.tokens if t.ttype is sqlparse.tokens.Keyword.DML), None)
        
        if not first_token or first_token.value.upper() != 'SELECT':
            raise ValidationError(
                _('Seules les requêtes SELECT sont autorisées'),
                code='not_select_query'
            )
            
    except Exception as e:
        raise ValidationError(
            _(f'Erreur de syntaxe SQL: {str(e)}'),
            code='invalid_sql'
        )
    
    return value


def validate_table_name(value):
    """
    Valide un nom de table
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Nom de table invalide. Utilisez lettres, chiffres et underscore'),
            code='invalid_table_name'
        )
    
    return value


def validate_column_name(value):
    """
    Valide un nom de colonne
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Nom de colonne invalide. Utilisez lettres, chiffres et underscore'),
            code='invalid_column_name'
        )
    
    return value


def validate_schema_name(value):
    """
    Valide un nom de schéma
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Nom de schéma invalide. Utilisez lettres, chiffres et underscore'),
            code='invalid_schema_name'
        )
    
    return value


def validate_json_schema(value):
    """
    Valide un schéma JSON
    """
    if not value:
        return value
    
    try:
        if isinstance(value, str):
            json.loads(value)
        elif isinstance(value, (dict, list)):
            json.dumps(value)
        else:
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        raise ValidationError(_('La valeur doit être un JSON valide'), code='invalid_json')
    
    return value


def validate_cron_expression(value):
    """
    Valide une expression CRON
    """
    if not value:
        return value
    
    parts = value.strip().split()
    if len(parts) not in [5, 6]:
        raise ValidationError(
            _('Expression CRON invalide. Utilisez 5 ou 6 champs: minute hour day month weekday [year]'),
            code='invalid_cron'
        )
    
    return value


def validate_timezone(value):
    """
    Valide un fuseau horaire
    """
    if not value:
        return value
    
    try:
        import pytz
        pytz.timezone(value)
        return value
    except ImportError:
        if value in ['UTC', 'Europe/Paris', 'America/New_York', 'Asia/Tokyo', 'Africa/Tunis']:
            return value
        raise ValidationError(_('Fuseau horaire invalide'), code='invalid_timezone')
    except pytz.UnknownTimeZoneError:
        raise ValidationError(_('Fuseau horaire inconnu'), code='unknown_timezone')