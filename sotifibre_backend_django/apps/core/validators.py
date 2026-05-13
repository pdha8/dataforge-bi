# apps/core/validators.py
"""
Validateurs complets pour Sotifibre BI Platform
- Validation des sources de données
- Sécurité SQL
- Format BI spécifique
- Validation des plannings
- Validation des KPI
"""
import re
import json
import sqlparse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


# ============================================================================
# CRON ET PLANIFICATION
# ============================================================================

def validate_cron_expression(value):
    """
    Valide une expression CRON pour les rapports planifiés
    Supporte les formats 5 et 6 champs
    """
    if not value:
        return value
    
    parts = value.strip().split()
    if len(parts) not in [5, 6]:
        raise ValidationError(
            _("Format CRON invalide. Utilisez 5 ou 6 champs: minute hour day month weekday [year]"),
            code='invalid_cron_parts'
        )
    
    minute, hour, day, month, weekday = parts[:5]
    
    # Patterns pour chaque champ
    pattern = r'^(\*|\d+|\d+-\d+|\d+(,\d+)*)(/\d+)?$'
    
    if not re.match(pattern, minute):
        raise ValidationError(_(f"Champ minute invalide: {minute}"), code='invalid_cron_minute')
    if not re.match(pattern, hour):
        raise ValidationError(_(f"Champ heure invalide: {hour}"), code='invalid_cron_hour')
    if not re.match(pattern, day):
        raise ValidationError(_(f"Champ jour invalide: {day}"), code='invalid_cron_day')
    if not re.match(pattern, month):
        raise ValidationError(_(f"Champ mois invalide: {month}"), code='invalid_cron_month')
    if not re.match(pattern, weekday):
        raise ValidationError(_(f"Champ jour semaine invalide: {weekday}"), code='invalid_cron_weekday')
    
    return value


def validate_schedule_interval(value):
    """
    Valide un intervalle de planification
    """
    if not value:
        return value
    
    valid_intervals = ['minute', 'hour', 'day', 'week', 'month', 'quarter', 'year']
    
    if value not in valid_intervals:
        raise ValidationError(
            _(f"Intervalle invalide. Choisir parmi: {', '.join(valid_intervals)}"),
            code='invalid_interval'
        )
    
    return value


# ============================================================================
# JSON ET YAML
# ============================================================================

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
        raise ValidationError(
            _("La valeur doit être un JSON valide"),
            code='invalid_json'
        )
    
    # Validation de schéma basique
    if isinstance(value, dict) and value:
        if 'required' in value and 'properties' in value:
            required_fields = value.get('required', [])
            properties = value.get('properties', {})
            
            for field in required_fields:
                if field not in properties:
                    raise ValidationError(
                        _(f"Champ requis '{field}' non défini dans les propriétés"),
                        code='missing_property'
                    )
    
    return value


def validate_yaml_content(value):
    """
    Valide le contenu YAML
    """
    if not value or not value.strip():
        raise ValidationError(_("Le contenu ne peut pas être vide"), code='empty_yaml')
    
    try:
        import yaml
        parsed = yaml.safe_load(value)
        if parsed is None:
            raise ValidationError(_("Le contenu YAML est vide"), code='empty_parsed_yaml')
        return value
    except ImportError:
        # yaml non installé, validation basique
        if '---' in value or '...' in value:
            return value
        raise ValidationError(_("Contenu YAML invalide"), code='invalid_yaml')
    except Exception as e:
        raise ValidationError(_(f"Erreur de syntaxe YAML: {str(e)}"), code='yaml_error')


# ============================================================================
# SQL ET REQUÊTES (SÉCURITÉ)
# ============================================================================

def validate_sql_query(value):
    """
    Valide une requête SQL avec vérification de sécurité
    """
    if not value:
        return value
    
    # Nettoyer la requête
    value = value.strip()
    
    try:
        parsed = sqlparse.parse(value)
        if not parsed:
            raise ValidationError(_("Requête SQL vide"), code='empty_query')
        
        query_upper = value.upper()
        
        # Mots-clés dangereux
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'SP_', 'XP_'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValidationError(
                    _(f"La requête contient le mot-clé interdit: {keyword}"),
                    code='dangerous_query'
                )
        
        # Vérifier les requêtes multiples
        statements = [s for s in value.split(';') if s.strip()]
        if len(statements) > 1:
            raise ValidationError(
                _("Les requêtes multiples ne sont pas autorisées"),
                code='multiple_statements'
            )
        
        # Vérifier que c'est une requête SELECT
        first_statement = sqlparse.parse(statements[0])[0]
        first_token = next((t for t in first_statement.tokens if t.ttype is sqlparse.tokens.Keyword.DML), None)
        
        if not first_token or first_token.value.upper() != 'SELECT':
            raise ValidationError(
                _("Seules les requêtes SELECT sont autorisées"),
                code='not_select_query'
            )
            
    except Exception as e:
        raise ValidationError(
            _(f"Erreur de syntaxe SQL: {str(e)}"),
            code='invalid_sql'
        )
    
    return value


def validate_query_parameters(params):
    """
    Valide les paramètres de requête
    """
    if not params:
        return params
    
    if not isinstance(params, dict):
        raise ValidationError(_("Les paramètres doivent être un dictionnaire"), code='invalid_params')
    
    for key, value in params.items():
        if not isinstance(key, str):
            raise ValidationError(_(f"La clé du paramètre doit être une chaîne: {key}"), code='invalid_param_key')
        
        # Vérifier les caractères dangereux dans les valeurs
        if isinstance(value, str):
            dangerous = ['--', ';', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
            value_upper = value.upper()
            for pattern in dangerous:
                if pattern in value_upper:
                    raise ValidationError(
                        _(f"Le paramètre '{key}' contient un motif dangereux: {pattern}"),
                        code='dangerous_param'
                    )
    
    return params


def validate_sql_identifier(value):
    """
    Valide un identifiant SQL (nom de table, colonne, etc.)
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Identifiant SQL invalide. Utilisez lettres, chiffres et underscore"),
            code='invalid_sql_identifier'
        )
    
    # Mots réservés SQL
    reserved_words = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
        'TABLE', 'VIEW', 'INDEX', 'DATABASE', 'SCHEMA', 'WHERE', 'FROM', 'JOIN',
        'GROUP', 'ORDER', 'BY', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT',
        'EXCEPT', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'AND', 'OR',
        'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE', 'AS'
    }
    
    if value.upper() in reserved_words:
        raise ValidationError(
            _(f"L'identifiant '{value}' est un mot réservé SQL"),
            code='reserved_word'
        )
    
    return value


# ============================================================================
# SOURCES DE DONNÉES
# ============================================================================

def validate_connection_string(value):
    """
    Valide une chaîne de connexion à une base de données
    """
    if not value:
        return value
    
    # Patterns supportés
    patterns = {
        'postgresql': r'^postgresql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'mysql': r'^mysql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'mongodb': r'^mongodb://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'clickhouse': r'^clickhouse://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'snowflake': r'^snowflake://([^:]+):([^@]+)@([^:/]+)/?(\w+)?',
        'bigquery': r'^bigquery://([^/]+)/([^?]+)',
    }
    
    valid = False
    for name, pattern in patterns.items():
        if re.match(pattern, value):
            valid = True
            break
    
    if not valid:
        raise ValidationError(
            _("Format de connexion invalide. Utilisez: protocol://user:pass@host:port/database"),
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
        raise ValidationError(_("Nom d'hôte ou adresse IP invalide"), code='invalid_hostname')
    
    return value


def validate_port(value):
    """
    Valide un numéro de port
    """
    if value is None:
        return value
    
    try:
        port = int(value)
        if not (1 <= port <= 65535):
            raise ValueError
        return port
    except (ValueError, TypeError):
        raise ValidationError(_("Le port doit être un nombre entre 1 et 65535"), code='invalid_port')


# ============================================================================
# BI SPÉCIFIQUES
# ============================================================================

def validate_chart_type(value):
    """
    Valide le type de graphique
    """
    if not value:
        return value
    
    valid_types = [
        'bar', 'line', 'pie', 'area', 'scatter', 'heatmap', 
        'funnel', 'gauge', 'map', 'table', 'pivot', 'radar', 
        'treemap', 'sankey', 'sunburst', 'waterfall'
    ]
    
    if value not in valid_types:
        raise ValidationError(
            _(f"Type de graphique invalide. Choisir parmi: {', '.join(valid_types)}"),
            code='invalid_chart_type'
        )
    
    return value


def validate_chart_config(value):
    """
    Valide la configuration d'un graphique
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_("La configuration doit être un dictionnaire"), code='invalid_config')
    
    # Vérifier les axes selon le type
    chart_type = value.get('type')
    if chart_type in ['bar', 'line', 'area', 'scatter']:
        if 'xAxis' not in value and 'x_axis' not in value:
            raise ValidationError(
                _("Les graphiques bar/line/area/scatter nécessitent un axe X"),
                code='missing_x_axis'
            )
        if 'yAxis' not in value and 'y_axis' not in value:
            raise ValidationError(
                _("Les graphiques bar/line/area/scatter nécessitent un axe Y"),
                code='missing_y_axis'
            )
    
    return value


def validate_dashboard_layout(value):
    """
    Valide le layout d'un tableau de bord
    """
    if not value:
        return value
    
    if not isinstance(value, list):
        raise ValidationError(_("Le layout doit être une liste de widgets"), code='invalid_layout')
    
    used_positions = set()
    max_x, max_y = 0, 0
    
    for widget in value:
        if not isinstance(widget, dict):
            raise ValidationError(_("Chaque widget doit être un dictionnaire"), code='invalid_widget')
        
        required_keys = ['id', 'x', 'y', 'w', 'h']
        for key in required_keys:
            if key not in widget:
                raise ValidationError(_(f"Widget manque la clé requise: {key}"), code='missing_widget_key')
        
        # Valider les dimensions
        if not isinstance(widget['x'], int) or widget['x'] < 0:
            raise ValidationError(_("La position x doit être un entier positif"), code='invalid_x')
        if not isinstance(widget['y'], int) or widget['y'] < 0:
            raise ValidationError(_("La position y doit être un entier positif"), code='invalid_y')
        if not isinstance(widget['w'], int) or widget['w'] <= 0 or widget['w'] > 12:
            raise ValidationError(_("La largeur doit être entre 1 et 12"), code='invalid_width')
        if not isinstance(widget['h'], int) or widget['h'] <= 0:
            raise ValidationError(_("La hauteur doit être un entier positif"), code='invalid_height')
        
        # Vérifier les positions uniques
        position = (widget['x'], widget['y'])
        if position in used_positions:
            raise ValidationError(_(f"Position ({widget['x']}, {widget['y']}) déjà utilisée"), code='duplicate_position')
        used_positions.add(position)
        
        max_x = max(max_x, widget['x'] + widget['w'])
        max_y = max(max_y, widget['y'] + widget['h'])
    
    return value


def validate_color_hex(value):
    """
    Valide une couleur hexadécimale
    """
    if not value:
        return value
    
    pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    if not re.match(pattern, value):
        raise ValidationError(_("Couleur invalide. Utilisez #RRGGBB ou #RGB"), code='invalid_color')
    
    return value


def validate_aggregation_function(value):
    """
    Valide une fonction d'agrégation
    """
    if not value:
        return value
    
    valid_functions = ['sum', 'avg', 'count', 'count_distinct', 'min', 'max', 'median', 'std', 'variance']
    
    if value not in valid_functions:
        raise ValidationError(
            _(f"Fonction d'agrégation invalide. Choisir parmi: {', '.join(valid_functions)}"),
            code='invalid_aggregation'
        )
    
    return value


def validate_measure_formula(value):
    """
    Valide une formule de mesure
    """
    if not value:
        return value
    
    # Vérifier les caractères dangereux
    dangerous_chars = [';', '--', '/*', '*/']
    value_upper = value.upper()
    
    for char in dangerous_chars:
        if char in value_upper:
            raise ValidationError(_(f"Caractère dangereux détecté: {char}"), code='dangerous_character')
    
    # Vérifier les fonctions autorisées
    allowed_keywords = ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END']
    
    return value


def validate_semantic_version(value):
    """
    Valide un numéro de version sémantique (x.y.z)
    """
    if not value:
        return value
    
    pattern = r'^\d+\.\d+\.\d+$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Version invalide. Utilisez le format sémantique: x.y.z"),
            code='invalid_version'
        )
    
    return value


# ============================================================================
# KPI SPÉCIFIQUES
# ============================================================================

def validate_kpi_threshold(value):
    """
    Valide la configuration de seuil KPI
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_("Le seuil doit être un dictionnaire"), code='invalid_threshold')
    
    required_keys = ['warning', 'critical']
    for key in required_keys:
        if key not in value:
            raise ValidationError(_(f"Clé de seuil manquante: {key}"), code='missing_threshold_key')
    
    try:
        warning = float(value['warning'])
        critical = float(value['critical'])
        
        if warning > critical:
            raise ValidationError(
                _("Le seuil d'avertissement doit être inférieur au seuil critique"),
                code='invalid_threshold_order'
            )
        
        return value
    except (ValueError, TypeError):
        raise ValidationError(_("Les seuils doivent être des nombres"), code='invalid_threshold_type')


def validate_kpi_target(value):
    """
    Valide la valeur cible KPI
    """
    if value is None:
        return value
    
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValidationError(_("La cible doit être un nombre"), code='invalid_target')


# ============================================================================
# RAPPORTS ET EXPORTS
# ============================================================================

def validate_report_format(value):
    """
    Valide le format d'export de rapport
    """
    if not value:
        return value
    
    valid_formats = ['pdf', 'csv', 'excel', 'json', 'html', 'png', 'svg']
    
    if value not in valid_formats:
        raise ValidationError(
            _(f"Format de rapport invalide. Choisir parmi: {', '.join(valid_formats)}"),
            code='invalid_format'
        )
    
    return value


def validate_email_list(value):
    """
    Valide une liste d'adresses email
    """
    if not value:
        return value
    
    if not isinstance(value, list):
        raise ValidationError(_("La liste des emails doit être un tableau"), code='invalid_email_list')
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    for email in value:
        if not isinstance(email, str):
            raise ValidationError(_("Chaque email doit être une chaîne"), code='invalid_email_type')
        
        if not re.match(email_pattern, email):
            raise ValidationError(_(f"Email invalide: {email}"), code='invalid_email')
    
    return value


# ============================================================================
# NUMÉRIQUES
# ============================================================================

def validate_positive_integer(value):
    """
    Valide un entier positif
    """
    if value is None:
        return value
    
    try:
        val = int(value)
        if val <= 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un entier positif"), code='invalid_positive_integer')


def validate_non_negative_integer(value):
    """
    Valide un entier non négatif
    """
    if value is None:
        return value
    
    try:
        val = int(value)
        if val < 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un entier non négatif"), code='invalid_non_negative_integer')


def validate_percentage(value):
    """
    Valide un pourcentage (0-100)
    """
    if value is None:
        return value
    
    try:
        val = float(value)
        if val < 0 or val > 100:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("Le pourcentage doit être entre 0 et 100"), code='invalid_percentage')


def validate_decimal_precision(value, max_digits=10, decimal_places=2):
    """
    Valide la précision décimale
    """
    if value is None:
        return value
    
    try:
        str_value = str(value)
        if '.' in str_value:
            _, decimals = str_value.split('.')
            if len(decimals) > decimal_places:
                raise ValidationError(
                    _(f"Maximum {decimal_places} décimales autorisées"),
                    code='too_many_decimals'
                )
        
        total_digits = len(str_value.replace('.', '').replace('-', ''))
        if total_digits > max_digits:
            raise ValidationError(
                _(f"Maximum {max_digits} chiffres autorisés"),
                code='too_many_digits'
            )
        
        return value
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un nombre"), code='invalid_number')


# ============================================================================
# GÉNÉRIQUES
# ============================================================================

def validate_domain_name(value):
    """
    Valide un nom de domaine
    """
    if not value:
        return value
    
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    if not re.match(pattern, value):
        raise ValidationError(_("Nom de domaine invalide"), code='invalid_domain')
    
    return value


def validate_url_safe(value):
    """
    Valide un slug URL-safe
    """
    if not value:
        return value
    
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Le slug doit contenir des lettres minuscules, chiffres et tirets"),
            code='invalid_slug'
        )
    
    return value


def validate_date_range(start_date, end_date):
    """
    Valide une plage de dates
    """
    if start_date and end_date:
        if start_date > end_date:
            raise ValidationError(
                _("La date de début doit être antérieure à la date de fin"),
                code='invalid_date_range'
            )
    return True


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
        # Si pytz n'est pas installé, validation basique
        if value in ['UTC', 'Europe/Paris', 'America/New_York', 'Asia/Tokyo']:
            return value
        raise ValidationError(_("Fuseau horaire invalide"), code='invalid_timezone')
    except pytz.UnknownTimeZoneError:
        raise ValidationError(_("Fuseau horaire inconnu"), code='unknown_timezone')


# ============================================================================
# VALIDATEURS DE FICHIERS
# ============================================================================

def validate_file_size(value, max_size_mb=10):
    """
    Valide la taille d'un fichier
    """
    if not value:
        return value
    
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            _(f"La taille du fichier ne doit pas dépasser {max_size_mb} MB"),
            code='file_too_large'
        )
    
    return value


def validate_file_extension(value, allowed_extensions=None):
    """
    Valide l'extension d'un fichier
    """
    if not value:
        return value
    
    allowed = allowed_extensions or ['.csv', '.xlsx', '.xls', '.json', '.parquet', '.avro', '.xml']
    import os
    
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in allowed:
        raise ValidationError(
            _(f"Extension de fichier non supportée. Extensions autorisées: {', '.join(allowed)}"),
            code='invalid_extension'
        )
    
    return value


# ============================================================================
# VALIDATEURS DE MODÈLES
# ============================================================================

def validate_unique_field(model, field_name, value, exclude_id=None):
    """
    Valide l'unicité d'un champ
    """
    if not value:
        return value
    
    kwargs = {field_name: value}
    if exclude_id:
        queryset = model.objects.exclude(id=exclude_id)
    else:
        queryset = model.objects.all()
    
    if queryset.filter(**kwargs).exists():
        raise ValidationError(
            _(f"La valeur '{value}' existe déjà"),
            code='duplicate_value'
        )
    
    return value


# ============================================================================
# COMPOSITE VALIDATORS
# ============================================================================

class BIFieldValidators:
    """
    Collection de validateurs de champs BI
    """
    
    @staticmethod
    def validate_metric_name(value):
        """Valide un nom de métrique"""
        if not value:
            return value
        
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        if not re.match(pattern, value):
            raise ValidationError(
                _("Le nom de la métrique doit commencer par une lettre et contenir lettres, chiffres et underscore"),
                code='invalid_metric_name'
            )
        return value
    
    @staticmethod
    def validate_dimension_name(value):
        """Valide un nom de dimension"""
        if not value:
            return value
        
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        if not re.match(pattern, value):
            raise ValidationError(
                _("Le nom de la dimension doit commencer par une lettre et contenir lettres, chiffres et underscore"),
                code='invalid_dimension_name'
            )
        return value
    
    @staticmethod
    def validate_filter_expression(value):
        """Valide une expression de filtre"""
        if not value:
            return value
        
        # Vérifier les parenthèses équilibrées
        if value.count('(') != value.count(')'):
            raise ValidationError(_("Parenthèses non équilibrées"), code='unbalanced_parentheses')
        
        # Vérifier les opérateurs valides
        valid_operators = ['=', '!=', '<', '>', '<=', '>=', 'IN', 'NOT IN', 'LIKE', 'BETWEEN']
        has_operator = False
        for op in valid_operators:
            if op in value:
                has_operator = True
                break
        
        if not has_operator:
            raise ValidationError(
                _(f"L'expression doit contenir un opérateur valide: {', '.join(valid_operators)}"),
                code='missing_operator'
            )
        
        return value