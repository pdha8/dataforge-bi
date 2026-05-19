# apps/notifications/consumers.py
"""
WebSocket consumers pour notifications temps réel
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications temps réel
    """
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            logger.warning(f"Tentative de connexion WebSocket non authentifiée")
            await self.close()
            return
        
        self.group_name = f"user_{self.user.id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer les notifications non lues
        await self.send_unread_count()
        logger.info(f"WebSocket connecté pour l'utilisateur {self.user.email}")
    
    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket déconnecté pour l'utilisateur {self.user.email}")
    
    async def receive(self, text_data):
        """Reçoit un message du client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                await self.send_unread_count()
            elif action == 'mark_all_read':
                await self.mark_all_notifications_read()
                await self.send_unread_count()
            elif action == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {e}")
        except Exception as e:
            logger.error(f"Erreur dans receive: {e}")
    
    async def notification_message(self, event):
        """Envoie une notification au client"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'data': event['notification']
            }))
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification: {e}")
    
    async def notification_count(self, event):
        """Envoie le compteur de notifications non lues"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'count',
                'data': event['count']
            }))
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du compteur: {e}")
    
    async def send_unread_count(self):
        """Envoie le nombre de notifications non lues"""
        try:
            count = await self.get_unread_count()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'notification_count',
                    'count': count
                }
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du compteur: {e}")
    
    @database_sync_to_async
    def get_unread_count(self):
        """Récupère le nombre de notifications non lues"""
        try:
            from .models import Notification
            return Notification.objects.unread(self.user).count()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du compteur: {e}")
            return 0
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marque une notification comme lue"""
        try:
            from .models import Notification
            notification = Notification.objects.get(id=notification_id, recipient=self.user)
            notification.mark_as_read()
            logger.debug(f"Notification {notification_id} marquée comme lue")
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} non trouvée")
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la notification: {e}")
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Marque toutes les notifications comme lues"""
        try:
            from .models import Notification
            count = Notification.objects.filter(
                recipient=self.user, 
                read_at__isnull=True
            ).update(read_at=timezone.now(), status='read')
            logger.info(f"{count} notifications marquées comme lues pour {self.user.email}")
        except Exception as e:
            logger.error(f"Erreur lors du marquage de toutes les notifications: {e}")