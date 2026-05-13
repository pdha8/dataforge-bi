# apps/notifications/models.py
"""
Notifications Models - Gestion des alertes et communications BI
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel
from apps.users.models import User
from apps.visualizations.models import Dashboard, KPI, Report
from apps.etl_engine.models import ETLPipeline

from .constants import (
    NOTIFICATION_TYPES, CHANNELS, NOTIFICATION_STATUS, PRIORITIES
)
from .validators import validate_email, validate_phone_number, validate_webhook_url
from .managers import NotificationManager, SubscriptionManager, AlertRuleManager, NotificationChannelManager


class Notification(BaseModel):
    """
    Notification individuelle
    """
    
    # Destinataire
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinataire'
    )
    
    # Contenu
    notification_type = models.CharField(
        'Type',
        max_length=50,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    title = models.CharField('Titre', max_length=200)
    message = models.TextField('Message')
    priority = models.CharField(
        'Priorité',
        max_length=20,
        choices=PRIORITIES,
        default='medium'
    )
    
    # Liens vers les objets concernés
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    pipeline = models.ForeignKey(
        ETLPipeline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_items',
        verbose_name='Pipeline ETL'
    )
    
    # Métadonnées
    metadata = models.JSONField('Métadonnées', default=dict, blank=True)
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=NOTIFICATION_STATUS,
        default='pending',
        db_index=True
    )
    
    # Canaux d'envoi
    channels = models.JSONField('Canaux', default=list, blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField('Envoyé le', null=True, blank=True)
    read_at = models.DateTimeField('Lu le', null=True, blank=True)
    delivered_at = models.DateTimeField('Livré le', null=True, blank=True)
    
    # Gestionnaire
    objects = NotificationManager()
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.email}"
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_delivered(self):
        """Marque la notification comme livrée"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def send(self, channel=None):
        """Envoie la notification"""
        from .services import NotificationService
        service = NotificationService()
        return service.send(self, channel)
    
    def get_icon(self):
        """Récupère l'icône selon le type"""
        icons = {
            'kpi_alert': '📊',
            'kpi_target_reached': '🎯',
            'pipeline_complete': '✅',
            'pipeline_failed': '❌',
            'pipeline_started': '🚀',
            'report_ready': '📄',
            'dashboard_shared': '🔗',
            'anomaly_detected': '🔍',
            'system_alert': '⚠️',
            'user_welcome': '👋',
            'weekly_digest': '📊',
        }
        return icons.get(self.notification_type, '🔔')
    
    def get_color(self):
        """Récupère la couleur selon la priorité"""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545',
        }
        return colors.get(self.priority, '#6c757d')


class NotificationChannel(BaseModel):
    """
    Canal de notification pour un utilisateur
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_channels',
        verbose_name='Utilisateur'
    )
    channel = models.CharField(
        'Canal',
        max_length=20,
        choices=CHANNELS,
        db_index=True
    )
    address = models.CharField(
        'Adresse',
        max_length=500,
        validators=[validate_email, validate_phone_number, validate_webhook_url]
    )
    is_enabled = models.BooleanField('Activé', default=True)
    is_verified = models.BooleanField('Vérifié', default=False)
    verification_token = models.CharField('Token', max_length=100, blank=True)
    verification_sent_at = models.DateTimeField('Token envoyé le', null=True, blank=True)
    last_used = models.DateTimeField('Dernier usage', null=True, blank=True)
    error_count = models.IntegerField('Nombre d\'erreurs', default=0)
    
    # Gestionnaire
    objects = NotificationChannelManager()
    
    class Meta:
        db_table = 'notification_channels'
        unique_together = ['user', 'channel']
        verbose_name = 'Canal de notification'
        verbose_name_plural = 'Canaux de notification'
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
            models.Index(fields=['channel', 'is_verified']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_channel_display()}"
    
    def verify(self, token):
        """Vérifie le canal"""
        if self.verification_token == token:
            self.is_verified = True
            self.save(update_fields=['is_verified'])
            return True
        return False
    
    def generate_verification_token(self):
        """Génère un token de vérification"""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_sent_at = timezone.now()
        self.save(update_fields=['verification_token', 'verification_sent_at'])
        return self.verification_token


class Subscription(BaseModel):
    """
    Abonnement d'un utilisateur à des notifications
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Utilisateur'
    )
    notification_type = models.CharField(
        'Type de notification',
        max_length=50,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    is_enabled = models.BooleanField('Activé', default=True)
    
    # Filtres spécifiques
    filters = models.JSONField('Filtres', default=dict, blank=True)
    
    # Canaux préférés pour ce type
    preferred_channels = models.JSONField('Canaux préférés', default=list, blank=True)
    
    # Gestionnaire
    objects = SubscriptionManager()
    
    class Meta:
        db_table = 'subscriptions'
        unique_together = ['user', 'notification_type']
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_notification_type_display()}"


class AlertRule(BaseModel):
    """
    Règle d'alerte pour les KPIs
    """
    
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    is_enabled = models.BooleanField('Activé', default=True)
    
    # KPI cible
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        related_name='alert_rules',
        verbose_name='KPI'
    )
    
    # Conditions
    CONDITION_CHOICES = [
        ('above', 'Au-dessus de'),
        ('below', 'En-dessous de'),
        ('equals', 'Égal à'),
        ('changed', 'Changement'),
        ('trend', 'Tendance'),
        ('percentage_change', 'Changement en pourcentage'),
    ]
    
    condition = models.CharField(
        'Condition',
        max_length=20,
        choices=CONDITION_CHOICES,
        default='above'
    )
    threshold = models.FloatField('Seuil', null=True, blank=True)
    percentage_change = models.FloatField('Changement en %', null=True, blank=True)
    
    # Période de vérification
    FREQUENCY_CHOICES = [
        ('minute', 'Chaque minute'),
        ('hourly', 'Horaire'),
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
    ]
    
    check_frequency = models.CharField(
        'Fréquence',
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='hourly'
    )
    
    # Cooldown pour éviter les alertes en spam
    cooldown_minutes = models.IntegerField('Cooldown (minutes)', default=60)
    last_triggered = models.DateTimeField('Dernier déclenchement', null=True, blank=True)
    trigger_count = models.IntegerField('Nombre de déclenchements', default=0)
    
    # Notification
    notification_channels = models.JSONField('Canaux de notification', default=list, blank=True)
    notification_message = models.TextField('Message personnalisé', blank=True)
    
    # Gestionnaire
    objects = AlertRuleManager()
    
    class Meta:
        db_table = 'alert_rules'
        verbose_name = 'Règle d\'alerte'
        verbose_name_plural = 'Règles d\'alerte'
        indexes = [
            models.Index(fields=['kpi', 'is_enabled']),
            models.Index(fields=['condition']),
            models.Index(fields=['last_triggered']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.kpi.name}"
    
    def evaluate(self, current_value, previous_value=None):
        """
        Évalue si la règle doit être déclenchée
        """
        if not self.is_enabled:
            return False
        
        # Vérifier le cooldown
        if self.last_triggered:
            cooldown_delta = timezone.now() - self.last_triggered
            if cooldown_delta.total_seconds() < self.cooldown_minutes * 60:
                return False
        
        triggered = False
        
        if self.condition == 'above' and self.threshold is not None:
            triggered = current_value > self.threshold
        
        elif self.condition == 'below' and self.threshold is not None:
            triggered = current_value < self.threshold
        
        elif self.condition == 'equals' and self.threshold is not None:
            triggered = abs(current_value - self.threshold) < 0.01
        
        elif self.condition == 'changed' and previous_value is not None:
            triggered = abs(current_value - previous_value) > 0.01
        
        elif self.condition == 'trend' and previous_value is not None:
            change = (current_value - previous_value) / previous_value * 100 if previous_value != 0 else 0
            triggered = abs(change) >= (self.percentage_change or 0)
        
        elif self.condition == 'percentage_change' and previous_value is not None:
            change = (current_value - previous_value) / previous_value * 100 if previous_value != 0 else 0
            if self.percentage_change is not None:
                if self.percentage_change > 0:
                    triggered = change >= self.percentage_change
                else:
                    triggered = change <= self.percentage_change
        
        if triggered:
            self.last_triggered = timezone.now()
            self.trigger_count += 1
            self.save(update_fields=['last_triggered', 'trigger_count'])
            
            # Créer la notification
            self._create_notification(current_value, previous_value)
        
        return triggered
    
    def _create_notification(self, current_value, previous_value):
        """
        Crée une notification pour cette alerte
        """
        from .services import NotificationService
        
        # Construire le message
        if self.notification_message:
            message = self.notification_message.format(
                kpi_name=self.kpi.name,
                current_value=current_value,
                previous_value=previous_value,
                threshold=self.threshold,
                change=self._calculate_change(current_value, previous_value)
            )
        else:
            message = self._get_default_message(current_value, previous_value)
        
        # Créer la notification
        service = NotificationService()
        notification = service.create_notification(
            recipient=self.kpi.owner,
            notification_type='kpi_alert',
            title=f"Alerte: {self.kpi.name}",
            message=message,
            priority='high' if self.condition in ['critical', 'above', 'below'] else 'medium',
            kpi=self.kpi,
            metadata={
                'rule_id': str(self.id),
                'rule_name': self.name,
                'current_value': current_value,
                'previous_value': previous_value,
                'condition': self.condition,
                'threshold': self.threshold
            }
        )
        
        # Envoyer via les canaux configurés
        channels = self.notification_channels or ['email']
        for channel in channels:
            notification.send(channel)
    
    def _calculate_change(self, current_value, previous_value):
        """Calcule le changement en pourcentage"""
        if previous_value and previous_value != 0:
            return (current_value - previous_value) / previous_value * 100
        return 0
    
    def _get_default_message(self, current_value, previous_value):
        """Message par défaut pour l'alerte"""
        change = self._calculate_change(current_value, previous_value)
        
        if self.condition == 'above':
            return f"Le KPI {self.kpi.name} est au-dessus du seuil ({current_value:.2f} > {self.threshold:.2f})"
        elif self.condition == 'below':
            return f"Le KPI {self.kpi.name} est en-dessous du seuil ({current_value:.2f} < {self.threshold:.2f})"
        elif self.condition == 'changed':
            return f"Le KPI {self.kpi.name} a changé de {change:+.1f}%"
        elif self.condition == 'trend':
            return f"Le KPI {self.kpi.name} a une tendance de {change:+.1f}%"
        elif self.condition == 'percentage_change':
            return f"Le KPI {self.kpi.name} a changé de {change:+.1f}% (seuil: {self.percentage_change}%)"
        
        return f"Alerte: {self.kpi.name} - Valeur: {current_value:.2f}"