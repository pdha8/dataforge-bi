"""
apps/ml_analytics/enums.py

Enums Python pour utilisation dans le code métier (services, tasks, etc.)
Séparés des choices Django pour éviter les imports lourds.
"""
from enum import Enum


class ModelType(str, Enum):
    FORECAST        = "forecast"
    ANOMALY         = "anomaly"
    SEGMENTATION    = "segmentation"
    RECOMMENDATION  = "recommendation"
    CLASSIFICATION  = "classification"
    REGRESSION      = "regression"
    CLUSTERING      = "clustering"
    TIME_SERIES     = "time_series"
    GROK_INSIGHT    = "grok_insight"


class Algorithm(str, Enum):
    PROPHET             = "prophet"
    ARIMA               = "arima"
    SARIMA              = "sarima"
    LSTM                = "lstm"
    XGBOOST             = "xgboost"
    GRADIENT_BOOSTING   = "gradient_boosting"
    RANDOM_FOREST       = "random_forest"
    ISOLATION_FOREST    = "isolation_forest"
    KMEANS              = "kmeans"
    DBSCAN              = "dbscan"
    HIERARCHICAL        = "hierarchical"
    SVM                 = "svm"
    LOGISTIC_REGRESSION = "logistic_regression"
    NEURAL_NETWORK      = "neural_network"
    GROK                = "grok"


class ModelStatus(str, Enum):
    PENDING    = "pending"
    TRAINING   = "training"
    TRAINED    = "trained"
    FAILED     = "failed"
    DEPLOYED   = "deployed"
    DEPRECATED = "deprecated"
    ARCHIVED   = "archived"


class TrainingFrequency(str, Enum):
    MANUAL  = "manual"
    HOURLY  = "hourly"
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"


class AnomalySeverity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class Priority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class RecommendationType(str, Enum):
    DASHBOARD = "dashboard"
    KPI       = "kpi"
    REPORT    = "report"
    INSIGHT   = "insight"
    ACTION    = "action"
