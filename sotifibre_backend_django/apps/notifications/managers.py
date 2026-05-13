# apps/notifications/managers.py
"""
Gestionnaires personnalisés pour l'application notifications
"""
from django.db import models
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta


class NotificationManager(models.Manager):
    """Gestionnaire personnalisé pour Notification"""
    
    def unread(self, user):
        """Notifications non lues d'un utilisateur"""
        return self.filter(recipient=user, status='sent', read_at__isnull=True)
    
    def for_user(self, user):
        """Notifications d'un utilisateur"""
        return self.filter(recipient=user)
    
    def pending(self):
        """Notifications en attente d'envoi"""
        return self.filter(status='pending')
    
    def failed(self):
        """Notifications échouées"""
        return self.filter(status='failed')
    
    def by_priority(self, priority):
        """Notifications par priorité"""
        return self.filter(priority=priority)
    
    def by_type(self, notification_type):
        """Notifications par type"""
        return self.filter(notification_type=notification_type)
    
    def recent(self, days=7):
        """Notifications récentes"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff)
    
    def stats(self, user=None):
        """Statistiques des notifications"""
        queryset = self.all()
        if user:
            queryset = queryset.filter(recipient=user)
        
        total = queryset.count()
        unread = queryset.filter(status='sent', read_at__isnull=True).count()
        by_type = dict(
            queryset.values_list('notification_type').annotate(count=Count('id'))
        )
        by_priority = dict(
            queryset.values_list('priority').annotate(count=Count('id'))
        )
        
        return {
            'total': total,
            'unread': unread,
            'by_type': by_type,
            'by_priority': by_priority,
        }


class SubscriptionManager(models.Manager):
    """Gestionnaire personnalisé pour Subscription"""
    
    def for_user(self, user):
        """Abonnements d'un utilisateur"""
        return self.filter(user=user, is_enabled=True)
    
    def enabled(self):
        """Abonnements activés"""
        return self.filter(is_enabled=True)
    
    def by_type(self, notification_type):
        """Abonnements par type"""
        return self.filter(notification_type=notification_type, is_enabled=True)
    
    def get_subscribers(self, notification_type, filters=None):
        """Récupère les abonnés à un type de notification"""
        queryset = self.filter(notification_type=notification_type, is_enabled=True)
        
        if filters:
            for key, value in filters.items():
                queryset = queryset.filter(filters__contains={key: value})
        
        return [sub.user for sub in queryset]


class AlertRuleManager(models.Manager):
    """Gestionnaire personnalisé pour AlertRule"""
    
    def enabled(self):
        """Règles activées"""
        return self.filter(is_enabled=True)
    
    def for_kpi(self, kpi):
        """Règles pour un KPI"""
        return self.filter(kpi=kpi, is_enabled=True)
    
    def needs_check(self):
        """Règles qui nécessitent une vérification"""
        rules = []
        for rule in self.enabled():
            # Vérifier le cooldown
            if rule.last_triggered:
                cooldown_delta = timezone.now() - rule.last_triggered
                if cooldown_delta.total_seconds() < rule.cooldown_minutes * 60:
                    continue
            
            # Vérifier la fréquence
            if rule.check_frequency == 'minute':
                rules.append(rule)
            elif rule.check_frequency == 'hourly':
                if rule.last_triggered and (timezone.now() - rule.last_triggered).seconds < 3600:
                    continue
                rules.append(rule)
            elif rule.check_frequency == 'daily':
                if rule.last_triggered and (timezone.now() - rule.last_triggered).days < 1:
                    continue
                rules.append(rule)
            elif rule.check_frequency == 'weekly':
                if rule.last_triggered and (timezone.now() - rule.last_triggered).days < 7:
                    continue
                rules.append(rule)
        
        return rules


class NotificationChannelManager(models.Manager):
    """Gestionnaire personnalisé pour NotificationChannel"""
    
    def for_user(self, user):
        """Canaux d'un utilisateur"""
        return self.filter(user=user, is_enabled=True)
    
    def enabled(self):
        """Canaux activés"""
        return self.filter(is_enabled=True)
    
    def verified(self):
        """Canaux vérifiés"""
        return self.filter(is_verified=True)
    
    def by_channel(self, channel):
        """Canaux par type"""
        return self.filter(channel=channel, is_enabled=True, is_verified=True)