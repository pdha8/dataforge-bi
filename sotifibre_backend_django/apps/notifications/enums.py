# apps/notifications/enums.py
"""
Enums pour l'application notifications
"""
from enum import Enum


class NotificationType(str, Enum):
    """Types de notifications"""
    KPI_ALERT = 'kpi_alert'
    KPI_TARGET_REACHED = 'kpi_target_reached'
    PIPELINE_COMPLETE = 'pipeline_complete'
    PIPELINE_FAILED = 'pipeline_failed'
    PIPELINE_STARTED = 'pipeline_started'
    REPORT_READY = 'report_ready'
    DASHBOARD_SHARED = 'dashboard_shared'
    DASHBOARD_EXPORTED = 'dashboard_exported'
    USER_MENTION = 'user_mention'
    COMMENT = 'comment'
    SYSTEM_ALERT = 'system_alert'
    DATA_REFRESH = 'data_refresh'
    ANOMALY_DETECTED = 'anomaly_detected'
    FORECAST_AVAILABLE = 'forecast_available'
    USER_WELCOME = 'user_welcome'
    PASSWORD_RESET = 'password_reset'
    EMAIL_VERIFICATION = 'email_verification'
    MAINTENANCE = 'maintenance'
    WEEKLY_DIGEST = 'weekly_digest'


class Channel(str, Enum):
    """Canaux de notification"""
    EMAIL = 'email'
    SMS = 'sms'
    PUSH = 'push'
    WEBHOOK = 'webhook'
    SLACK = 'slack'
    TEAMS = 'teams'
    TELEGRAM = 'telegram'
    WHATSAPP = 'whatsapp'


class NotificationStatus(str, Enum):
    """Statuts des notifications"""
    PENDING = 'pending'
    QUEUED = 'queued'
    SENT = 'sent'
    FAILED = 'failed'
    DELIVERED = 'delivered'
    READ = 'read'
    ARCHIVED = 'archived'


class Priority(str, Enum):
    """Priorités"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'