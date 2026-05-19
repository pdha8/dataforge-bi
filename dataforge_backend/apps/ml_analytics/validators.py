"""
apps/ml_analytics/validators.py

Validateurs Django pour les champs JSONField des modèles ML Analytics.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_model_config(value: dict) -> dict:
    """
    Valide la configuration JSON d'un modèle ML.
    - Doit être un dict
    - Les clés autorisées sont vérifiées si 'strict' est True
    """
    if not value:
        return value
    if not isinstance(value, dict):
        raise ValidationError(
            _("La configuration du modèle doit être un dictionnaire JSON."),
            code="invalid_type",
        )
    # Clés réservées interdites
    reserved_keys = {"__class__", "__module__", "__import__"}
    bad_keys = reserved_keys & set(value.keys())
    if bad_keys:
        raise ValidationError(
            _("Clés de configuration non autorisées : %(keys)s"),
            code="reserved_keys",
            params={"keys": ", ".join(bad_keys)},
        )
    return value


def validate_forecast_params(value: dict) -> dict:
    """
    Valide les paramètres de prévision.
    - horizon : entier positif
    - confidence_level : entier entre 0 et 100
    """
    if not value:
        return value
    if not isinstance(value, dict):
        raise ValidationError(
            _("Les paramètres de prévision doivent être un dictionnaire JSON."),
            code="invalid_type",
        )
    horizon = value.get("horizon")
    if horizon is not None:
        if not isinstance(horizon, int) or horizon <= 0:
            raise ValidationError(
                _("Le paramètre 'horizon' doit être un entier strictement positif."),
                code="invalid_horizon",
            )
        if horizon > 3650:
            raise ValidationError(
                _("Le paramètre 'horizon' ne peut pas dépasser 3 650 jours (10 ans)."),
                code="horizon_too_large",
            )
    confidence_level = value.get("confidence_level")
    if confidence_level is not None:
        if not isinstance(confidence_level, (int, float)) or not (0 < confidence_level <= 100):
            raise ValidationError(
                _("'confidence_level' doit être un nombre entre 1 et 100."),
                code="invalid_confidence",
            )
    return value


def validate_tags(value: list) -> list:
    """
    Valide les tags d'un modèle ML.
    - Doit être une liste de chaînes
    - Maximum 20 tags
    - Chaque tag : max 50 caractères
    """
    if not value:
        return value
    if not isinstance(value, list):
        raise ValidationError(
            _("Les tags doivent être une liste JSON."),
            code="invalid_type",
        )
    if len(value) > 20:
        raise ValidationError(
            _("Un modèle ne peut pas avoir plus de 20 tags."),
            code="too_many_tags",
        )
    for tag in value:
        if not isinstance(tag, str):
            raise ValidationError(
                _("Chaque tag doit être une chaîne de caractères."),
                code="invalid_tag_type",
            )
        if len(tag) > 50:
            raise ValidationError(
                _("Un tag ne peut pas dépasser 50 caractères."),
                code="tag_too_long",
            )
    return value
