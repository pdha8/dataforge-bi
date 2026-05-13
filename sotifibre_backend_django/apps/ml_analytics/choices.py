"""
apps/ml_analytics/choices.py

Re-exporte toutes les constantes de choix pour utilisation dans les modèles,
serializers et filtres sans import circulaire.
"""
from .constants import (
    ALGORITHMS,
    ANOMALY_SEVERITY,
    CONFIDENCE_LEVELS,
    FORECAST_PERIODS,
    MODEL_STATUS,
    MODEL_TYPES,
    PRIORITY_LEVELS,
    RECOMMENDATION_TYPES,
    TRAINING_FREQUENCIES,
    TRAINING_LOG_STATUS,
)

__all__ = [
    "ALGORITHMS",
    "ANOMALY_SEVERITY",
    "CONFIDENCE_LEVELS",
    "FORECAST_PERIODS",
    "MODEL_STATUS",
    "MODEL_TYPES",
    "PRIORITY_LEVELS",
    "RECOMMENDATION_TYPES",
    "TRAINING_FREQUENCIES",
    "TRAINING_LOG_STATUS",
]