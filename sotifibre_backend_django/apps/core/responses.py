# apps/core/responses.py
"""
Réponses standardisées pour Sotifibre BI
"""
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone


def success_response(data=None, message="Succès", status_code=status.HTTP_200_OK, meta=None):
    """Réponse de succès standard avec métadonnées optionnelles"""
    response_data = {
        "status": True,
        "message": message,
        "data": data,
        "timestamp": timezone.now().isoformat(),
    }
    
    if meta:
        response_data["meta"] = meta
    
    return Response(response_data, status=status_code)


def created_response(data=None, message="Créé avec succès", meta=None):
    """Réponse 201 Créé"""
    return success_response(data, message, status.HTTP_201_CREATED, meta)


def error_response(message="Une erreur est survenue", errors=None, status_code=status.HTTP_400_BAD_REQUEST, code=None):
    """Réponse d'erreur standard"""
    response_data = {
        "status": False,
        "message": message,
        "timestamp": timezone.now().isoformat(),
    }
    
    if errors:
        response_data["errors"] = errors
    
    if code:
        response_data["code"] = code
    
    return Response(response_data, status=status_code)


def not_found_response(message="Ressource non trouvée", resource_type=None, resource_id=None):
    """Réponse 404 Non trouvé"""
    errors = {}
    if resource_type and resource_id:
        errors = {resource_type: f"{resource_id} non trouvé(e)"}
    
    return error_response(
        message=message,
        errors=errors,
        status_code=status.HTTP_404_NOT_FOUND,
        code="not_found"
    )


def forbidden_response(message="Permission refusée", required_permission=None):
    """Réponse 403 Interdit"""
    errors = {}
    if required_permission:
        errors["required"] = required_permission
    
    return error_response(
        message=message,
        errors=errors,
        status_code=status.HTTP_403_FORBIDDEN,
        code="forbidden"
    )


def validation_error_response(errors, message="Erreur de validation"):
    """Réponse 422 Erreur de validation"""
    return error_response(
        message=message,
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error"
    )


def conflict_response(message="Conflit de ressource", details=None):
    """Réponse 409 Conflit"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_409_CONFLICT,
        code="conflict"
    )


def unauthorized_response(message="Non authentifié", details=None):
    """Réponse 401 Non autorisé"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="unauthorized"
    )


def bad_request_response(message="Requête invalide", details=None):
    """Réponse 400 Mauvaise requête"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_400_BAD_REQUEST,
        code="bad_request"
    )


def server_error_response(message="Erreur interne du serveur", details=None):
    """Réponse 500 Erreur serveur"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="server_error"
    )


def service_unavailable_response(message="Service temporairement indisponible", details=None):
    """Réponse 503 Service indisponible"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="service_unavailable"
    )


# ========================================================================
# RÉPONSES SPÉCIFIQUES BI
# ========================================================================

def bi_data_response(data, metadata=None):
    """Réponse avec métadonnées BI"""
    response_data = {
        "data": data,
        "metadata": metadata or {
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "platform": "Sotifibre BI"
        }
    }
    return success_response(response_data, "Données BI récupérées")


def chart_data_response(data, chart_config=None):
    """Réponse pour données de graphique"""
    response_data = {
        "data": data,
        "chart_config": chart_config or {},
        "timestamp": timezone.now().isoformat()
    }
    return success_response(response_data, "Données de graphique récupérées")


def dashboard_response(dashboard_data, layout=None):
    """Réponse pour tableau de bord"""
    response_data = {
        "dashboard": dashboard_data,
        "layout": layout or {},
        "last_refresh": timezone.now().isoformat()
    }
    return success_response(response_data, "Tableau de bord récupéré")