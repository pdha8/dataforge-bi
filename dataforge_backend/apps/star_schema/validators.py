# apps/star_schema/validators.py
"""
Validateurs pour l'application star_schema
"""
import re
import json
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_schema_name(value):
    """Valide le nom d'un schéma"""
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Nom de schéma invalide. Utilisez lettres, chiffres et underscore'),
            code='invalid_schema_name'
        )
    
    return value


def validate_relation_definition(value):
    """Valide une définition de relation"""
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('La relation doit être un dictionnaire'), code='invalid_relation')
    
    required_keys = ['from_table', 'from_column', 'to_table', 'to_column']
    for key in required_keys:
        if key not in value:
            raise ValidationError(_(f'Clé requise manquante: {key}'), code='missing_key')
    
    return value


def validate_dimension_mapping(value):
    """Valide le mapping des dimensions"""
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('Le mapping doit être un dictionnaire'), code='invalid_mapping')
    
    for dim_name, columns in value.items():
        if not isinstance(dim_name, str):
            raise ValidationError(_('Le nom de la dimension doit être une chaîne'), code='invalid_dimension_name')
        
        if not isinstance(columns, (list, dict)):
            raise ValidationError(
                _('Les colonnes doivent être une liste ou un dictionnaire'),
                code='invalid_columns'
            )
    
    return value


def validate_measure_definition(value):
    """Valide une définition de mesure"""
    if not value:
        return value
    
    if not isinstance(value, list):
        raise ValidationError(_('Les mesures doivent être une liste'), code='invalid_measures')
    
    for measure in value:
        if not isinstance(measure, dict):
            raise ValidationError(_('Chaque mesure doit être un dictionnaire'), code='invalid_measure')
        
        required_keys = ['name', 'column', 'aggregation']
        for key in required_keys:
            if key not in measure:
                raise ValidationError(_(f'Mesure manque la clé: {key}'), code='missing_measure_key')
    
    return value


def validate_filter_expression(value):
    """Valide une expression de filtre"""
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('Le filtre doit être un dictionnaire'), code='invalid_filter')
    
    if 'field' not in value:
        raise ValidationError(_('Le filtre doit contenir un champ'), code='missing_field')
    
    if 'operator' not in value:
        raise ValidationError(_('Le filtre doit contenir un opérateur'), code='missing_operator')
    
    return value


def validate_calculation_formula(value):
    """Valide une formule de calcul"""
    if not value:
        return value
    
    # Vérifier les caractères dangereux
    dangerous_chars = [';', '--', '/*', '*/', 'DROP', 'DELETE']
    value_upper = value.upper()
    
    for char in dangerous_chars:
        if char in value_upper:
            raise ValidationError(_(f'Caractère dangereux détecté: {char}'), code='dangerous_character')
    
    # Vérifier les parenthèses équilibrées
    if value.count('(') != value.count(')'):
        raise ValidationError(_('Parenthèses non équilibrées'), code='unbalanced_parentheses')
    
    return value


def validate_schema_graph(value):
    """Valide le graphe du schéma"""
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('Le graphe doit être un dictionnaire'), code='invalid_graph')
    
    if 'nodes' not in value or 'edges' not in value:
        raise ValidationError(
            _('Le graphe doit contenir des nœuds et des arêtes'),
            code='missing_graph_components'
        )
    
    return value