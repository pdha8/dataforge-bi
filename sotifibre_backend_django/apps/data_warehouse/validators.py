# apps/data_warehouse/validators.py
"""
Validateurs personnalisés pour l'application data_warehouse
"""
import re
import json
import sqlparse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_table_name(value):
    """
    Valide un nom de table Data Warehouse
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Nom de table invalide. Utilisez lettres, chiffres et underscore'),
            code='invalid_table_name'
        )
    
    # Vérifier la longueur
    if len(value) > 63:
        raise ValidationError(
            _('Le nom de table ne peut pas dépasser 63 caractères'),
            code='table_name_too_long'
        )
    
    return value


def validate_column_name(value):
    """
    Valide un nom de colonne Data Warehouse
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Nom de colonne invalide. Utilisez lettres, chiffres et underscore'),
            code='invalid_column_name'
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
            _(f'Le nom de colonne "{value}" est un mot réservé SQL'),
            code='reserved_word'
        )
    
    return value


def validate_sql_query(value):
    """
    Valide une requête SQL pour le Data Warehouse
    """
    if not value:
        return value
    
    value = value.strip()
    
    try:
        parsed = sqlparse.parse(value)
        if not parsed:
            raise ValidationError(_('Requête SQL vide'), code='empty_query')
        
        # Vérifier les mots-clés dangereux
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        query_upper = value.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValidationError(
                    _(f'La requête contient le mot-clé interdit: {keyword}'),
                    code='dangerous_query'
                )
        
        # Vérifier que c'est une requête SELECT
        first_statement = sqlparse.parse(value)[0]
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


def validate_partition_expression(value):
    """
    Valide une expression de partitionnement
    """
    if not value:
        return value
    
    # Vérifier les formats valides
    patterns = [
        r'^RANGE\s*\([^)]+\)$',
        r'^LIST\s*\([^)]+\)$',
        r'^HASH\s*\([^)]+\)$',
        r'^BY\s+RANGE\s*\([^)]+\)$',
        r'^BY\s+LIST\s*\([^)]+\)$',
        r'^BY\s+HASH\s*\([^)]+\)$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, value, re.IGNORECASE):
            return value
    
    raise ValidationError(
        _('Expression de partition invalide. Utilisez: RANGE(col), LIST(col), HASH(col)'),
        code='invalid_partition_expression'
    )


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


def validate_measure_formula(value):
    """
    Valide une formule de mesure
    """
    if not value:
        return value
    
    # Vérifier les caractères dangereux
    dangerous_chars = [';', '--', '/*', '*/']
    for char in dangerous_chars:
        if char in value:
            raise ValidationError(
                _(f'Caractère dangereux détecté: {char}'),
                code='dangerous_character'
            )
    
    # Vérifier les fonctions autorisées
    allowed_functions = [
        'SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'DISTINCT',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'COALESCE', 'NULLIF'
    ]
    
    value_upper = value.upper()
    # Validation basique - on pourrait ajouter plus de vérifications
    
    return value


def validate_granularity(value):
    """
    Valide une granularité
    """
    valid_granularities = [
        'transaction', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    ]
    
    if value not in valid_granularities:
        raise ValidationError(
            _(f'Granularité invalide. Choisir parmi: {", ".join(valid_granularities)}'),
            code='invalid_granularity'
        )
    
    return value


def validate_scd_type(value):
    """
    Valide un type SCD
    """
    valid_scd = ['type0', 'type1', 'type2', 'type3', 'type4', 'type6']
    
    if value not in valid_scd:
        raise ValidationError(
            _(f'Type SCD invalide. Choisir parmi: {", ".join(valid_scd)}'),
            code='invalid_scd_type'
        )
    
    return value