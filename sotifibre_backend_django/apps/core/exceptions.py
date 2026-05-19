# apps/core/exceptions.py
"""
Gestionnaire d'exceptions personnalisé pour Sotifibre BI
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour Sotifibre
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "status": False,
            "message": "Une erreur est survenue.",
            "errors": {},
        }

        if hasattr(response, "data"):
            data = response.data
            if isinstance(data, dict):
                if "detail" in data:
                    error_data["message"] = str(data["detail"])
                elif "message" in data:
                    error_data["message"] = str(data["message"])
                else:
                    error_data["errors"] = data
                    error_data["message"] = "Erreur de validation."
            elif isinstance(data, list):
                error_data["errors"] = {"non_field_errors": data}
                error_data["message"] = str(data[0]) if data else "Erreur."

        status_code = response.status_code
        if status_code == 400:
            error_data["code"] = "bad_request"
        elif status_code == 401:
            error_data["code"] = "unauthorized"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Non authentifié."
        elif status_code == 403:
            error_data["code"] = "forbidden"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Permission refusée."
        elif status_code == 404:
            error_data["code"] = "not_found"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Ressource non trouvée."
        elif status_code == 405:
            error_data["code"] = "method_not_allowed"
            error_data["message"] = "Méthode non autorisée."
        elif status_code == 409:
            error_data["code"] = "conflict"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Conflit de ressource."
        elif status_code == 422:
            error_data["code"] = "validation_error"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Erreur de validation."
        elif status_code == 429:
            error_data["code"] = "too_many_requests"
            error_data["message"] = "Trop de requêtes. Veuillez réessayer plus tard."
        elif status_code >= 500:
            error_data["code"] = "server_error"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Erreur interne du serveur."

        response.data = error_data
        
    else:
        logger.exception("Exception non gérée: %s", exc)
        
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Erreur interne du serveur."
        code = "server_error"
        
        if isinstance(exc, Http404):
            status_code = status.HTTP_404_NOT_FOUND
            message = "Ressource non trouvée."
            code = "not_found"
        elif isinstance(exc, PermissionDenied):
            status_code = status.HTTP_403_FORBIDDEN
            message = "Permission refusée."
            code = "forbidden"
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Erreur de validation."
            code = "validation_error"
            error_data = {
                "status": False,
                "message": message,
                "errors": exc.message_dict if hasattr(exc, 'message_dict') else exc.messages,
                "code": code,
            }
            from django.utils import timezone
            error_data["timestamp"] = timezone.now().isoformat()
            return Response(error_data, status=status_code)
        
        response = Response(
            {
                "status": False,
                "message": message,
                "errors": {},
                "code": code,
            },
            status=status_code,
        )
        
        from django.utils import timezone
        response.data["timestamp"] = timezone.now().isoformat()

    return response


# ========================================================================
# EXCEPTIONS SPÉCIFIQUES SOTIFIBRE
# ========================================================================

class SotifibreException(Exception):
    """Exception de base pour DataForge"""
    
    def __init__(self, message="Une erreur DataForge est survenue", code=None, status_code=400):
        self.message = message
        self.code = code or "dataforge_error"
        self.status_code = status_code
        super().__init__(self.message)


class DataSourceNotFoundException(SotifibreException):
    """Exception pour source de données non trouvée"""
    
    def __init__(self, source_id=None, message=None):
        if not message:
            message = f"Source de données non trouvée" + (f" : {source_id}" if source_id else "")
        super().__init__(message, code="data_source_not_found", status_code=404)


class ConnectionFailedException(SotifibreException):
    """Exception pour échec de connexion"""
    
    def __init__(self, reason=None, message=None):
        if not message:
            message = f"Échec de connexion" + (f" : {reason}" if reason else "")
        super().__init__(message, code="connection_failed", status_code=500)


class QueryExecutionException(SotifibreException):
    """Exception pour échec d'exécution de requête"""
    
    def __init__(self, query=None, message=None):
        if not message:
            message = f"Erreur d'exécution de requête" + (f" : {query}" if query else "")
        super().__init__(message, code="query_execution_error", status_code=400)


class InvalidQueryException(SotifibreException):
    """Exception pour requête invalide"""
    
    def __init__(self, reason=None, message=None):
        if not message:
            message = f"Requête invalide" + (f" : {reason}" if reason else "")
        super().__init__(message, code="invalid_query", status_code=400)


class DashboardNotFoundException(SotifibreException):
    """Exception pour tableau de bord non trouvé"""
    
    def __init__(self, dashboard_id=None, message=None):
        if not message:
            message = f"Tableau de bord non trouvé" + (f" : {dashboard_id}" if dashboard_id else "")
        super().__init__(message, code="dashboard_not_found", status_code=404)


class VisualizationNotFoundException(SotifibreException):
    """Exception pour visualisation non trouvée"""
    
    def __init__(self, viz_id=None, message=None):
        if not message:
            message = f"Visualisation non trouvée" + (f" : {viz_id}" if viz_id else "")
        super().__init__(message, code="visualization_not_found", status_code=404)


class KPINotFoundException(SotifibreException):
    """Exception pour KPI non trouvé"""
    
    def __init__(self, kpi_id=None, message=None):
        if not message:
            message = f"KPI non trouvé" + (f" : {kpi_id}" if kpi_id else "")
        super().__init__(message, code="kpi_not_found", status_code=404)


class ETLPipelineException(SotifibreException):
    """Exception pour pipeline ETL"""
    
    def __init__(self, pipeline_id=None, message=None):
        if not message:
            message = f"Erreur dans le pipeline ETL" + (f" : {pipeline_id}" if pipeline_id else "")
        super().__init__(message, code="etl_pipeline_error", status_code=500)


class ExportException(SotifibreException):
    """Exception pour export de données"""
    
    def __init__(self, format=None, message=None):
        if not message:
            message = f"Erreur d'export" + (f" au format {format}" if format else "")
        super().__init__(message, code="export_error", status_code=500)


class DataWarehouseException(SotifibreException):
    """Exception pour entrepôt de données"""
    
    def __init__(self, reason=None, message=None):
        if not message:
            message = f"Erreur Data Warehouse" + (f" : {reason}" if reason else "")
        super().__init__(message, code="data_warehouse_error", status_code=500)


class SchemaException(SotifibreException):
    """Exception pour schéma invalide"""
    
    def __init__(self, schema_name=None, message=None):
        if not message:
            message = f"Schéma invalide" + (f" : {schema_name}" if schema_name else "")
        super().__init__(message, code="schema_error", status_code=400)