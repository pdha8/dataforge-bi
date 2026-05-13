# apps/visualizations/validators.py
"""
Validateurs pour l'application visualizations
"""
import re
import json
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_chart_config(value):
    """
    Valide la configuration d'un graphique
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('La configuration doit être un dictionnaire'), code='invalid_config')
    
    # Vérifier les clés minimales
    required_keys = ['type']
    for key in required_keys:
        if key not in value:
            raise ValidationError(_(f'Clé requise manquante: {key}'), code='missing_key')
    
    # Vérifier le type de graphique
    valid_chart_types = [
        'bar', 'line', 'pie', 'area', 'scatter', 'heatmap',
        'funnel', 'gauge', 'map', 'table', 'pivot', 'radar',
        'treemap', 'sankey', 'sunburst', 'waterfall', 'box', 'histogram'
    ]
    
    if value['type'] not in valid_chart_types:
        raise ValidationError(
            _(f'Type de graphique invalide. Choisir parmi: {", ".join(valid_chart_types)}'),
            code='invalid_chart_type'
        )
    
    return value


def validate_dashboard_layout(value):
    """
    Valide le layout d'un tableau de bord
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('Le layout doit être un dictionnaire'), code='invalid_layout')
    
    # Vérifier la structure de la grille
    if 'grid' in value:
        grid = value['grid']
        if not isinstance(grid, list):
            raise ValidationError(_('La grille doit être une liste'), code='invalid_grid')
        
        for item in grid:
            if not isinstance(item, dict):
                raise ValidationError(_('Chaque élément de grille doit être un dictionnaire'), code='invalid_grid_item')
            
            required_keys = ['x', 'y', 'w', 'h']
            for key in required_keys:
                if key not in item:
                    raise ValidationError(_(f'Élément de grille manque la clé: {key}'), code='missing_grid_key')
            
            # Valider les dimensions
            if not isinstance(item['x'], int) or item['x'] < 0:
                raise ValidationError(_('La position x doit être un entier positif'), code='invalid_x')
            if not isinstance(item['y'], int) or item['y'] < 0:
                raise ValidationError(_('La position y doit être un entier positif'), code='invalid_y')
            if not isinstance(item['w'], int) or item['w'] <= 0 or item['w'] > 12:
                raise ValidationError(_('La largeur doit être entre 1 et 12'), code='invalid_width')
            if not isinstance(item['h'], int) or item['h'] <= 0:
                raise ValidationError(_('La hauteur doit être un entier positif'), code='invalid_height')
    
    return value


def validate_kpi_config(value):
    """
    Valide la configuration d'un KPI
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('La configuration doit être un dictionnaire'), code='invalid_config')
    
    # Vérifier le type de KPI
    valid_kpi_types = ['number', 'percentage', 'currency', 'ratio', 'trend', 'comparison']
    
    if 'type' in value and value['type'] not in valid_kpi_types:
        raise ValidationError(
            _(f'Type de KPI invalide. Choisir parmi: {", ".join(valid_kpi_types)}'),
            code='invalid_kpi_type'
        )
    
    return value


def validate_filter_expression(value):
    """
    Valide une expression de filtre
    """
    if not value:
        return value
    
    if not isinstance(value, (list, dict)):
        raise ValidationError(_('Le filtre doit être une liste ou un dictionnaire'), code='invalid_filter')
    
    def validate_single_filter(filter_item):
        if not isinstance(filter_item, dict):
            return False
        
        if 'field' not in filter_item:
            return False
        
        if 'operator' not in filter_item:
            return False
        
        valid_operators = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'like', 'between', 'is_null']
        if filter_item['operator'] not in valid_operators:
            return False
        
        return True
    
    if isinstance(value, list):
        for item in value:
            if not validate_single_filter(item):
                raise ValidationError(_('Filtre invalide'), code='invalid_filter_structure')
    elif isinstance(value, dict):
        if not validate_single_filter(value):
            raise ValidationError(_('Filtre invalide'), code='invalid_filter_structure')
    
    return value


def validate_color_hex(value):
    """
    Valide une couleur hexadécimale
    """
    if not value:
        return value
    
    pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    if not re.match(pattern, value):
        raise ValidationError(_('Couleur invalide. Utilisez #RRGGBB ou #RGB'), code='invalid_color')
    
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


def validate_email_list(value):
    """
    Valide une liste d'emails
    """
    if not value:
        return value
    
    if not isinstance(value, list):
        raise ValidationError(_('La liste des emails doit être un tableau'), code='invalid_email_list')
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    for email in value:
        if not isinstance(email, str):
            raise ValidationError(_('Chaque email doit être une chaîne'), code='invalid_email_type')
        
        if not re.match(email_pattern, email):
            raise ValidationError(_(f'Email invalide: {email}'), code='invalid_email')
    
    return value