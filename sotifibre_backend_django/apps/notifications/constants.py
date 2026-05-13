# apps/notifications/constants.py
"""
Constantes pour l'application notifications
"""

# ============================================================================
# TYPES DE NOTIFICATIONS
# ============================================================================
NOTIFICATION_TYPES = [
    ('kpi_alert', '📊 Alerte KPI'),
    ('kpi_target_reached', '🎯 Objectif KPI atteint'),
    ('pipeline_complete', '✅ Pipeline ETL terminé'),
    ('pipeline_failed', '❌ Pipeline ETL échoué'),
    ('pipeline_started', '🚀 Pipeline ETL démarré'),
    ('report_ready', '📄 Rapport prêt'),
    ('dashboard_shared', '🔗 Dashboard partagé'),
    ('dashboard_exported', '📤 Dashboard exporté'),
    ('user_mention', '👤 Mention'),
    ('comment', '💬 Commentaire'),
    ('system_alert', '⚠️ Alerte système'),
    ('data_refresh', '🔄 Données rafraîchies'),
    ('anomaly_detected', '🔍 Anomalie détectée'),
    ('forecast_available', '📈 Prévision disponible'),
    ('user_welcome', '👋 Bienvenue'),
    ('password_reset', '🔐 Réinitialisation mot de passe'),
    ('email_verification', '✉️ Vérification email'),
    ('maintenance', '🔧 Maintenance planifiée'),
    ('weekly_digest', '📊 Digest hebdomadaire'),
]

# ============================================================================
# CANAUX DE NOTIFICATION
# ============================================================================
CHANNELS = [
    ('email', '📧 Email'),
    ('sms', '📱 SMS'),
    ('push', '📲 Push'),
    ('webhook', '🌐 Webhook'),
    ('slack', '💬 Slack'),
    ('teams', '💼 Microsoft Teams'),
    ('telegram', '✈️ Telegram'),
    ('whatsapp', '💚 WhatsApp'),
]

# ============================================================================
# STATUTS DES NOTIFICATIONS
# ============================================================================
NOTIFICATION_STATUS = [
    ('pending', '⏳ En attente'),
    ('queued', '📤 En file d\'attente'),
    ('sent', '✅ Envoyé'),
    ('failed', '❌ Échoué'),
    ('delivered', '📬 Livré'),
    ('read', '📖 Lu'),
    ('archived', '📦 Archivé'),
]

# ============================================================================
# PRIORITÉS
# ============================================================================
PRIORITIES = [
    ('low', '🟢 Basse'),
    ('medium', '🟡 Moyenne'),
    ('high', '🟠 Haute'),
    ('critical', '🔴 Critique'),
]

# ============================================================================
# TEMPLATES DE NOTIFICATION
# ============================================================================
EMAIL_TEMPLATES = {
    'kpi_alert': 'notifications/emails/kpi_alert.html',
    'pipeline_complete': 'notifications/emails/pipeline_complete.html',
    'pipeline_failed': 'notifications/emails/pipeline_failed.html',
    'report_ready': 'notifications/emails/report_ready.html',
    'dashboard_shared': 'notifications/emails/dashboard_shared.html',
    'anomaly_detected': 'notifications/emails/anomaly_detected.html',
    'user_welcome': 'notifications/emails/user_welcome.html',
    'password_reset': 'notifications/emails/password_reset.html',
    'email_verification': 'notifications/emails/email_verification.html',
    'weekly_digest': 'notifications/emails/weekly_digest.html',
}

# ============================================================================
# SMS TEMPLATES
# ============================================================================
SMS_TEMPLATES = {
    'kpi_alert': "Alerte KPI: {kpi_name} - {status} - {value} {unit}",
    'pipeline_failed': "Pipeline ETL échoué: {pipeline_name}",
    'pipeline_complete': "Pipeline ETL terminé: {pipeline_name}",
    'anomaly_detected': "Anomalie détectée: {description}",
}

# ============================================================================
# PUSH NOTIFICATION TEMPLATES
# ============================================================================
PUSH_TEMPLATES = {
    'kpi_alert': {
        'title': '📊 Alerte KPI',
        'body': '{kpi_name} - {status} - {value} {unit}',
        'icon': '/static/icons/kpi_alert.png',
    },
    'pipeline_failed': {
        'title': '❌ Pipeline ETL échoué',
        'body': 'Le pipeline {pipeline_name} a échoué',
        'icon': '/static/icons/pipeline_failed.png',
    },
    'report_ready': {
        'title': '📄 Rapport prêt',
        'body': 'Votre rapport {report_name} est prêt',
        'icon': '/static/icons/report_ready.png',
    },
}