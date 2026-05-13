# apps/notifications/validators.py
"""
Validateurs pour l'application notifications
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_email(value):
    """Valide une adresse email"""
    if not value:
        return value
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValidationError(_('Adresse email invalide'), code='invalid_email')
    
    return value


def validate_phone_number(value):
    """Valide un numéro de téléphone"""
    if not value:
        return value
    
    pattern = r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
    if not re.match(pattern, value):
        raise ValidationError(_('Numéro de téléphone invalide'), code='invalid_phone')
    
    return value


def validate_webhook_url(value):
    """Valide une URL de webhook"""
    if not value:
        return value
    
    pattern = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, value):
        raise ValidationError(_('URL de webhook invalide'), code='invalid_webhook')
    
    return value


def validate_cron_expression(value):
    """Valide une expression CRON"""
    if not value:
        return value
    
    parts = value.strip().split()
    if len(parts) not in [5, 6]:
        raise ValidationError(
            _('Expression CRON invalide. Utilisez 5 ou 6 champs'),
            code='invalid_cron'
        )
    
    return value