# apps/notifications/services.py
"""
Services pour l'application notifications
"""
import json
import logging
import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

# Import conditionnel pour channels
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    get_channel_layer = None
    async_to_sync = None

# Import conditionnel des packages
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None

try:
    from slack_sdk import WebClient as SlackClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    SlackClient = None

try:
    import pymsteams
    TEAMS_AVAILABLE = True
except ImportError:
    TEAMS_AVAILABLE = False

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    TelegramError = None

from .models import Notification, NotificationChannel, Subscription, AlertRule
from .constants import EMAIL_TEMPLATES, SMS_TEMPLATES, PUSH_TEMPLATES

logger = logging.getLogger(__name__)


class NotificationService:
    """Service principal de notification"""
    
    def __init__(self):
        self.twilio_client = None
        if TWILIO_AVAILABLE and hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID:
            self.twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        
        self.slack_client = None
        if SLACK_AVAILABLE and hasattr(settings, 'SLACK_BOT_TOKEN') and settings.SLACK_BOT_TOKEN:
            self.slack_client = SlackClient(token=settings.SLACK_BOT_TOKEN)
        
        self.telegram_bot = None
        if TELEGRAM_AVAILABLE and hasattr(settings, 'TELEGRAM_BOT_TOKEN') and settings.TELEGRAM_BOT_TOKEN:
            self.telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    def create_notification(self, recipient, notification_type, title, message, 
                           priority='medium', channels=None, **kwargs):
        """Crée une notification"""
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            channels=channels or ['email'],
            **kwargs
        )
        
        # Envoyer immédiatement
        for channel in (channels or ['email']):
            self.send(notification, channel)
        
        return notification
    
    def send(self, notification, channel='email'):
        """Envoie une notification via un canal spécifique"""
        try:
            if channel == 'email':
                result = self._send_email(notification)
            elif channel == 'sms':
                result = self._send_sms(notification)
            elif channel == 'push':
                result = self._send_push(notification)
            elif channel == 'slack':
                result = self._send_slack(notification)
            elif channel == 'teams':
                result = self._send_teams(notification)
            elif channel == 'telegram':
                result = self._send_telegram(notification)
            elif channel == 'webhook':
                result = self._send_webhook(notification)
            else:
                result = {'success': False, 'error': f'Canal non supporté: {channel}'}
            
            if result['success']:
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save(update_fields=['status', 'sent_at'])
                
                # Envoyer via WebSocket en temps réel
                self._send_websocket(notification)
                
            else:
                logger.error(f"Échec d'envoi {channel}: {result.get('error')}")
                
                if notification.status == 'pending':
                    notification.status = 'failed'
                    notification.save(update_fields=['status'])
            
            return result
            
        except Exception as e:
            logger.exception(f"Erreur lors de l'envoi de la notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_email(self, notification):
        """Envoie un email"""
        try:
            template_name = EMAIL_TEMPLATES.get(
                notification.notification_type, 
                'notifications/emails/default.html'
            )
            
            context = {
                'notification': notification,
                'title': notification.title,
                'message': notification.message,
                'user': notification.recipient,
                'dashboard': notification.dashboard,
                'kpi': notification.kpi,
                'report': notification.report,
                'metadata': notification.metadata,
                'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
            }
            
            html_content = render_to_string(template_name, context)
            text_content = notification.message
            
            # Utiliser SendGrid si configuré
            if hasattr(settings, 'ANYMAIL') and settings.ANYMAIL.get('SENDGRID_API_KEY'):
                from django.core.mail import EmailMultiAlternatives
                email = EmailMultiAlternatives(
                    subject=notification.title,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[notification.recipient.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            else:
                send_mail(
                    subject=notification.title,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient.email],
                    html_message=html_content,
                    fail_silently=False,
                )
            
            return {'success': True, 'channel': 'email'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_sms(self, notification):
        """Envoie un SMS via Twilio"""
        if not TWILIO_AVAILABLE or not self.twilio_client:
            return {'success': False, 'error': 'Twilio non configuré'}
        
        try:
            template = SMS_TEMPLATES.get(notification.notification_type, "{message}")
            
            message = template.format(
                kpi_name=notification.kpi.name if notification.kpi else "",
                pipeline_name=notification.pipeline.name if notification.pipeline else "",
                report_name=notification.report.name if notification.report else "",
                status=notification.metadata.get('status', ''),
                value=notification.metadata.get('value', ''),
                unit=notification.metadata.get('unit', ''),
                description=notification.message
            )
            
            if len(message) > 160:
                message = message[:157] + "..."
            
            channel = NotificationChannel.objects.filter(
                user=notification.recipient,
                channel='sms',
                is_enabled=True,
                is_verified=True
            ).first()
            
            if not channel:
                return {'success': False, 'error': 'Aucun canal SMS configuré'}
            
            self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=channel.address
            )
            
            return {'success': True, 'channel': 'sms'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_push(self, notification):
        """Envoie une notification push"""
        try:
            template = PUSH_TEMPLATES.get(notification.notification_type, {
                'title': notification.title,
                'body': notification.message
            })
            
            title = template.get('title', notification.title)
            body = template.get('body', notification.message).format(
                kpi_name=notification.kpi.name if notification.kpi else "",
                pipeline_name=notification.pipeline.name if notification.pipeline else "",
                report_name=notification.report.name if notification.report else "",
                status=notification.metadata.get('status', ''),
                value=notification.metadata.get('value', ''),
                unit=notification.metadata.get('unit', '')
            )
            
            # TODO: Intégrer Firebase Cloud Messaging
            logger.info(f"Push notification: {title} - {body}")
            
            return {'success': True, 'channel': 'push'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_slack(self, notification):
        """Envoie une notification Slack"""
        if not SLACK_AVAILABLE or not self.slack_client:
            return {'success': False, 'error': 'Slack non configuré'}
        
        try:
            channel = NotificationChannel.objects.filter(
                user=notification.recipient,
                channel='slack',
                is_enabled=True,
                is_verified=True
            ).first()
            
            if not channel:
                return {'success': False, 'error': 'Aucun canal Slack configuré'}
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": notification.title,
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": notification.message
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Type: {notification.get_notification_type_display()} | Priorité: {notification.get_priority_display()}"
                        }
                    ]
                }
            ]
            
            if notification.dashboard:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Voir le dashboard",
                                "emoji": True
                            },
                            "url": f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard/{notification.dashboard.id}"
                        }
                    ]
                })
            
            response = self.slack_client.chat_postMessage(
                channel=channel.address,
                blocks=blocks,
                text=notification.title
            )
            
            if response.get('ok'):
                return {'success': True, 'channel': 'slack'}
            else:
                return {'success': False, 'error': response.get('error', 'Erreur inconnue')}
            
        except SlackApiError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_teams(self, notification):
        """Envoie une notification Microsoft Teams"""
        if not TEAMS_AVAILABLE:
            return {'success': False, 'error': 'pymsteams non installé'}
        
        try:
            channel = NotificationChannel.objects.filter(
                user=notification.recipient,
                channel='teams',
                is_enabled=True,
                is_verified=True
            ).first()
            
            if not channel:
                return {'success': False, 'error': 'Aucun canal Teams configuré'}
            
            teams_message = pymsteams.connectorcard(channel.address)
            teams_message.title(notification.title)
            teams_message.text(notification.message)
            
            section = pymsteams.cardsection()
            section.addFact("Type", notification.get_notification_type_display())
            section.addFact("Priorité", notification.get_priority_display())
            section.addFact("Date", notification.created_at.strftime("%d/%m/%Y %H:%M"))
            teams_message.addSection(section)
            
            if notification.dashboard:
                teams_message.addLinkButton("Voir le dashboard", f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard/{notification.dashboard.id}")
            
            teams_message.send()
            
            return {'success': True, 'channel': 'teams'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_telegram(self, notification):
        """Envoie une notification Telegram"""
        if not TELEGRAM_AVAILABLE or not self.telegram_bot:
            return {'success': False, 'error': 'Telegram non configuré'}
        
        try:
            channel = NotificationChannel.objects.filter(
                user=notification.recipient,
                channel='telegram',
                is_enabled=True,
                is_verified=True
            ).first()
            
            if not channel:
                return {'success': False, 'error': 'Aucun canal Telegram configuré'}
            
            # Formater le message avec Markdown
            message = f"""
*{notification.title}*
{notification.message}

📌 *Type:* {notification.get_notification_type_display()}
⚡ *Priorité:* {notification.get_priority_display()}
🕐 *Date:* {notification.created_at.strftime('%d/%m/%Y %H:%M')}
            """
            
            # Envoyer le message
            self.telegram_bot.send_message(
                chat_id=channel.address,
                text=message,
                parse_mode='Markdown'
            )
            
            return {'success': True, 'channel': 'telegram'}
            
        except TelegramError as e:
            return {'success': False, 'error': f'Telegram error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_webhook(self, notification):
        """Envoie une notification via webhook"""
        try:
            channel = NotificationChannel.objects.filter(
                user=notification.recipient,
                channel='webhook',
                is_enabled=True,
                is_verified=True
            ).first()
            
            if not channel:
                return {'success': False, 'error': 'Aucun webhook configuré'}
            
            payload = {
                'id': str(notification.id),
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'timestamp': notification.created_at.isoformat(),
                'metadata': notification.metadata
            }
            
            retry_count = getattr(settings, 'WEBHOOK_RETRY_COUNT', 3)
            timeout = getattr(settings, 'WEBHOOK_TIMEOUT_SECONDS', 10)
            
            for attempt in range(retry_count):
                try:
                    response = requests.post(
                        channel.address, 
                        json=payload, 
                        timeout=timeout
                    )
                    response.raise_for_status()
                    return {'success': True, 'channel': 'webhook'}
                except requests.exceptions.RequestException as e:
                    if attempt == retry_count - 1:
                        raise e
                    continue
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_websocket(self, notification):
        """Envoie une notification via WebSocket (temps réel)"""
        if not CHANNELS_AVAILABLE:
            logger.debug("Channels non disponible, WebSocket désactivé")
            return
        
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                # Vérifier que async_to_sync est disponible
                if async_to_sync:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{notification.recipient.id}",
                        {
                            'type': 'notification_message',
                            'notification': {
                                'id': str(notification.id),
                                'title': notification.title,
                                'message': notification.message,
                                'type': notification.notification_type,
                                'priority': notification.priority,
                                'icon': notification.get_icon(),
                                'color': notification.get_color(),
                                'created_at': notification.created_at.isoformat()
                            }
                        }
                    )
        except Exception as e:
            logger.error(f"Erreur WebSocket: {e}")
    
    def mark_as_read(self, notification_id, user):
        """Marque une notification comme lue"""
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.mark_as_read()
        return notification


class AlertRuleService:
    """Service de vérification des règles d'alerte"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def check_all_rules(self):
        """Vérifie toutes les règles d'alerte"""
        rules = AlertRule.objects.needs_check()
        
        for rule in rules:
            self.check_rule(rule)
    
    def check_rule(self, rule):
        """Vérifie une règle spécifique"""
        try:
            from apps.visualizations.services import KPIService
            kpi_service = KPIService(rule.kpi)
            result = kpi_service.calculate()
            
            if result['success']:
                current_value = result['value']
                previous_value = result.get('previous_value')
                
                rule.evaluate(current_value, previous_value)
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la règle {rule.id}: {e}")