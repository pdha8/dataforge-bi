# apps/etl_engine/validators.py
"""
Validateurs personnalisés pour l'application etl_engine
"""
import re
import json
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cron_expression(value):
    """
    Valide une expression CRON pour la planification
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


def validate_python_code(value):
    """
    Valide du code Python (syntaxe)
    """
    if not value:
        return value
    
    try:
        compile(value, '<string>', 'exec')
    except SyntaxError as e:
        raise ValidationError(
            _(f'Erreur de syntaxe Python: {str(e)}'),
            code='invalid_python'
        )
    
    # Vérifier les fonctions dangereuses
    dangerous_imports = ['os', 'subprocess', 'sys', 'eval', 'exec', '__import__']
    for dangerous in dangerous_imports:
        if dangerous in value:
            raise ValidationError(
                _(f'Le code contient un import dangereux: {dangerous}'),
                code='dangerous_import'
            )
    
    return value


def validate_sql_code(value):
    """
    Valide du code SQL (syntaxe basique)
    """
    if not value:
        return value
    
    # Vérifier les mots-clés dangereux
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
        'TRUNCATE', 'GRANT', 'REVOKE'
    ]
    
    value_upper = value.upper()
    for keyword in dangerous_keywords:
        if keyword in value_upper:
            raise ValidationError(
                _(f'Le code SQL contient le mot-clé dangereux: {keyword}'),
                code='dangerous_sql'
            )
    
    return value


def validate_transformation_config(value):
    """
    Valide la configuration d'une transformation
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('La configuration doit être un dictionnaire'), code='invalid_config')
    
    required_keys = ['type', 'config']
    for key in required_keys:
        if key not in value:
            raise ValidationError(_(f'Clé requise manquante: {key}'), code='missing_key')
    
    return value


def validate_dependency_graph(value):
    """
    Valide un graphe de dépendances
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('Le graphe doit être un dictionnaire'), code='invalid_graph')
    
    # Vérifier l'absence de cycles
    nodes = set(value.keys())
    visited = set()
    stack = set()
    
    def has_cycle(node):
        visited.add(node)
        stack.add(node)
        
        for dep in value.get(node, []):
            if dep not in visited:
                if has_cycle(dep):
                    return True
            elif dep in stack:
                return True
        
        stack.remove(node)
        return False
    
    for node in nodes:
        if node not in visited:
            if has_cycle(node):
                raise ValidationError(_('Cycle détecté dans les dépendances'), code='cycle_detected')
    
    return value


def validate_retry_policy(value):
    """
    Valide une politique de réessai
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('La politique doit être un dictionnaire'), code='invalid_policy')
    
    required_keys = ['max_retries', 'delay_seconds', 'backoff_factor']
    for key in required_keys:
        if key not in value:
            raise ValidationError(_(f'Clé requise manquante: {key}'), code='missing_key')
    
    if not isinstance(value['max_retries'], int) or value['max_retries'] < 0:
        raise ValidationError(_('max_retries doit être un entier positif'), code='invalid_max_retries')
    
    if not isinstance(value['delay_seconds'], (int, float)) or value['delay_seconds'] < 0:
        raise ValidationError(_('delay_seconds doit être un nombre positif'), code='invalid_delay')
    
    if not isinstance(value['backoff_factor'], (int, float)) or value['backoff_factor'] < 1:
        raise ValidationError(_('backoff_factor doit être >= 1'), code='invalid_backoff')
    
    return value