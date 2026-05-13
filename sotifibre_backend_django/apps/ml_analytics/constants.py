"""
apps/ml_analytics/constants.py

Toutes les constantes utilisées dans l'application ML Analytics.
"""

MODEL_TYPES: list[tuple[str, str]] = [
    ("forecast",        "📈 Prévision"),
    ("anomaly",         "🔍 Détection d'anomalies"),
    ("segmentation",    "👥 Segmentation"),
    ("recommendation",  "💡 Recommandation"),
    ("classification",  "🏷️ Classification"),
    ("regression",      "📊 Régression"),
    ("clustering",      "🔵 Clustering"),
    ("time_series",     "⏱️ Série temporelle"),
    ("grok_insight",    "🤖 Grok Insight"),
]

ALGORITHMS: list[tuple[str, str]] = [
    ("prophet",           "Prophet (Facebook)"),
    ("arima",             "ARIMA"),
    ("sarima",            "SARIMA"),
    ("lstm",              "LSTM (Deep Learning)"),
    ("xgboost",           "XGBoost"),
    ("gradient_boosting", "Gradient Boosting"),
    ("random_forest",     "Random Forest"),
    ("isolation_forest",  "Isolation Forest"),
    ("kmeans",            "K-Means"),
    ("dbscan",            "DBSCAN"),
    ("hierarchical",      "Hierarchical Clustering"),
    ("svm",               "SVM"),
    ("logistic_regression", "Régression Logistique"),
    ("neural_network",    "Réseau de Neurones"),
    ("grok",              "🤖 Grok AI (xAI)"),
]

MODEL_STATUS: list[tuple[str, str]] = [
    ("pending",    "⏳ En attente"),
    ("training",   "🏋️ Entraînement"),
    ("trained",    "✅ Entraîné"),
    ("failed",     "❌ Échoué"),
    ("deployed",   "🚀 Déployé"),
    ("deprecated", "⚠️ Obsolète"),
    ("archived",   "📦 Archivé"),
]

TRAINING_FREQUENCIES: list[tuple[str, str]] = [
    ("manual",  "👤 Manuel"),
    ("hourly",  "🕓 Horaire"),
    ("daily",   "📅 Quotidien"),
    ("weekly",  "📆 Hebdomadaire"),
    ("monthly", "🗓️ Mensuel"),
]

FORECAST_PERIODS: list[tuple[str, str]] = [
    ("day",     "Jour"),
    ("week",    "Semaine"),
    ("month",   "Mois"),
    ("quarter", "Trimestre"),
    ("year",    "Année"),
]

CONFIDENCE_LEVELS: list[tuple[int, str]] = [
    (80, "80%"),
    (85, "85%"),
    (90, "90%"),
    (95, "95%"),
    (99, "99%"),
]

RECOMMENDATION_TYPES: list[tuple[str, str]] = [
    ("dashboard", "📊 Tableau de bord"),
    ("kpi",       "📈 KPI"),
    ("report",    "📄 Rapport"),
    ("insight",   "💡 Insight"),
    ("action",    "⚡ Action"),
]

ANOMALY_SEVERITY: list[tuple[str, str]] = [
    ("low",      "🟢 Faible"),
    ("medium",   "🟡 Moyenne"),
    ("high",     "🟠 Haute"),
    ("critical", "🔴 Critique"),
]

PRIORITY_LEVELS: list[tuple[str, str]] = [
    ("low",    "Basse"),
    ("medium", "Moyenne"),
    ("high",   "Haute"),
]

TRAINING_LOG_STATUS: list[tuple[str, str]] = [
    ("started",     "Démarré"),
    ("in_progress", "En cours"),
    ("completed",   "Terminé"),
    ("failed",      "Échoué"),
]

# Seuils de qualité (en %)
QUALITY_THRESHOLDS = {
    "excellent":   95.0,
    "good":        85.0,
    "acceptable":  70.0,
}

# Nombre maximum de points envoyés à Grok
GROK_MAX_DATA_POINTS = 200

# Horizon de prévision par défaut (jours)
DEFAULT_FORECAST_HORIZON = 30
