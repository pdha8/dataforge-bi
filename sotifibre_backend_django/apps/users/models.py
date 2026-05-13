# apps/users/models.py
"""
Users Models with Roles and Permissions for Sotifibre BI Platform
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from apps.core.models import BaseModel
from apps.core.utils import generate_hash
import uuid


class UserManager(BaseUserManager):
    """Gestionnaire personnalisé pour User Sotifibre"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'email est requis')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        extra_fields.setdefault('status', 'active')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    """
    Modèle utilisateur étendu pour Sotifibre BI
    """
    
    # Rôles BI
    ROLE_CHOICES = [
        ('superadmin', '👑 Super Administrateur BI'),
        ('admin', '⚙️ Administrateur BI'),
        ('bi_analyst', '📊 Analyste BI'),
        ('bi_developer', '💻 Développeur BI'),
        ('bi_consumer', '📱 Consommateur BI'),
        ('viewer', '👀 Observateur'),
    ]
    
    STATUS_CHOICES = [
        ('active', '✅ Actif'),
        ('inactive', '⏸️ Inactif'),
        ('suspended', '🚫 Suspendu'),
        ('locked', '🔒 Verrouillé'),
    ]
    
    # Override username to make it non-unique (use email as unique)
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    
    # Role and Status
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='bi_consumer', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Profile
    phone = models.CharField('Téléphone', max_length=20, blank=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', null=True, blank=True)
    department = models.CharField('Département', max_length=100, blank=True)
    job_title = models.CharField('Poste', max_length=100, blank=True)
    employee_id = models.CharField('Matricule', max_length=50, unique=True, null=True, blank=True)
    
    # Security
    is_verified = models.BooleanField('Vérifié', default=False)
    two_factor_enabled = models.BooleanField('2FA activé', default=False)
    failed_login_attempts = models.IntegerField('Tentatives échouées', default=0)
    account_locked_until = models.DateTimeField('Compte verrouillé jusqu\'au', null=True, blank=True)
    last_login_ip = models.GenericIPAddressField('Dernière IP', null=True, blank=True)
    
    # API Access
    api_access_enabled = models.BooleanField('Accès API', default=True)
    api_rate_limit = models.IntegerField('Limite API', default=1000, help_text="Requêtes par heure")
    
    # Preferences BI
    timezone = models.CharField('Fuseau horaire', max_length=50, default='UTC')
    language = models.CharField('Langue', max_length=10, default='fr')
    theme = models.CharField('Thème', max_length=20, default='light', 
                           choices=[('light', 'Clair'), ('dark', 'Sombre')])
    
    # Activity tracking
    last_activity_at = models.DateTimeField('Dernière activité', null=True, blank=True)
    date_joined = models.DateTimeField('Date d\'inscription', auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    # ========================================================================
    # PROPRIÉTÉS DE RÔLE POUR SOTIFIBRE BI
    # ========================================================================
    
    @property
    def is_admin(self):
        """Superadmin ou Admin"""
        return self.role in ['superadmin', 'admin']
    
    @property
    def is_superadmin(self):
        """Superadmin uniquement"""
        return self.role == 'superadmin'
    
    # 🗄️ Sources de données
    @property
    def can_manage_data_sources(self):
        """Gérer les sources de données"""
        return self.role in ['superadmin', 'admin', 'bi_developer']
    
    @property
    def can_view_data_sources(self):
        """Voir les sources de données"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst', 'bi_consumer']
    
    # 🔄 ETL
    @property
    def can_manage_etl(self):
        """Gérer les pipelines ETL"""
        return self.role in ['superadmin', 'admin', 'bi_developer']
    
    @property
    def can_view_etl(self):
        """Voir les pipelines ETL"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    # 📊 Visualisations
    @property
    def can_manage_visualizations(self):
        """Gérer les visualisations"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    @property
    def can_view_visualizations(self):
        """Voir les visualisations"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst', 'bi_consumer']
    
    # 📈 Tableaux de bord
    @property
    def can_manage_dashboards(self):
        """Gérer les tableaux de bord"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    @property
    def can_view_dashboards(self):
        """Voir les tableaux de bord"""
        return True
    
    @property
    def can_create_dashboards(self):
        """Créer des tableaux de bord"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    @property
    def can_share_dashboards(self):
        """Partager des tableaux de bord"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    # 🎯 KPIs
    @property
    def can_manage_kpis(self):
        """Gérer les KPIs"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    @property
    def can_view_kpis(self):
        """Voir les KPIs"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst', 'bi_consumer']
    
    # 📤 Export
    @property
    def can_export_data(self):
        """Exporter les données"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    # 📅 Planification
    @property
    def can_schedule_reports(self):
        """Planifier des rapports"""
        return self.role in ['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    
    # 🔔 Notifications
    @property
    def can_view_notifications(self):
        """Voir les notifications"""
        return True
    
    @property
    def can_manage_notifications(self):
        """Gérer les notifications"""
        return self.role in ['superadmin', 'admin']
    
    # 💾 Import/Export
    @property
    def can_import_data(self):
        """Importer des données"""
        return self.role in ['superadmin', 'admin', 'bi_developer']
    
    # 🔧 Utilitaires
    @property
    def is_account_locked(self):
        if self.account_locked_until:
            from django.utils import timezone
            return timezone.now() < self.account_locked_until
        return False
    
    def increment_failed_attempts(self):
        """Augmente le compteur d'échecs de connexion"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from django.utils import timezone
            from datetime import timedelta
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
            self.status = 'locked'
        self.save()
    
    def reset_failed_attempts(self):
        """Réinitialise le compteur d'échecs"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        if self.status == 'locked':
            self.status = 'active'
        self.save()


class Team(BaseModel):
    """Équipes pour organiser les utilisateurs BI"""
    name = models.CharField('Nom', max_length=100, unique=True)
    description = models.TextField('Description', blank=True)
    team_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='led_teams', verbose_name='Chef d\'équipe')
    members = models.ManyToManyField(User, related_name='teams', blank=True, 
                                     verbose_name='Membres')
    
    class Meta:
        db_table = 'teams'
        verbose_name = 'Équipe'
        verbose_name_plural = 'Équipes'
    
    def __str__(self):
        return self.name


class Permission(BaseModel):
    """Permissions personnalisées pour Sotifibre BI"""
    
    CATEGORY_CHOICES = [
        ('core', '🔧 Core'),
        ('users', '👥 Utilisateurs'),
        ('data_sources', '🗄️ Sources de données'),
        ('etl', '🔄 ETL'),
        ('warehouse', '🏢 Entrepôt'),
        ('visualizations', '📊 Visualisations'),
        ('dashboards', '📈 Tableaux de bord'),
        ('kpis', '🎯 KPIs'),
        ('reports', '📑 Rapports'),
        ('notifications', '🔔 Notifications'),
        ('admin', '⚙️ Administration'),
    ]
    
    code = models.CharField('Code', max_length=100, unique=True, db_index=True)
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    category = models.CharField('Catégorie', max_length=50, choices=CATEGORY_CHOICES)
    
    class Meta:
        db_table = 'permissions'
        ordering = ['category', 'code']
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class Role(BaseModel):
    """Rôles avec permissions associées pour Sotifibre BI"""
    name = models.CharField('Nom', max_length=100, unique=True)
    description = models.TextField('Description', blank=True)
    permissions = models.JSONField('Permissions', default=list, 
                                  help_text="Liste des codes de permission")
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
    
    def __str__(self):
        return self.name
    
    def has_permission(self, permission_code):
        return permission_code in self.permissions
    
    def add_permission(self, permission_code):
        if permission_code not in self.permissions:
            self.permissions.append(permission_code)
            self.save()
    
    def remove_permission(self, permission_code):
        if permission_code in self.permissions:
            self.permissions.remove(permission_code)
            self.save()


class UserActivity(BaseModel):
    """Journal des activités utilisateur pour Sotifibre BI"""
    
    ACTION_CHOICES = [
        ('login', '🔑 Connexion'),
        ('logout', '🚪 Déconnexion'),
        ('create', '➕ Création'),
        ('update', '📝 Modification'),
        ('delete', '🗑️ Suppression'),
        ('view', '👀 Visualisation'),
        ('export', '📤 Export'),
        ('import', '📥 Import'),
        ('share', '🔗 Partage'),
        ('schedule', '📅 Planification'),
        ('dashboard_create', '📊 Création dashboard'),
        ('dashboard_share', '🔗 Partage dashboard'),
        ('data_source_test', '🔌 Test source données'),
        ('etl_run', '🔄 Exécution ETL'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', '🟢 Faible'),
        ('medium', '🟡 Moyenne'),
        ('high', '🟠 Élevée'),
        ('critical', '🔴 Critique'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', 
                            verbose_name='Utilisateur')
    action = models.CharField('Action', max_length=30, choices=ACTION_CHOICES)
    severity = models.CharField('Sévérité', max_length=20, choices=SEVERITY_CHOICES, default='low')
    
    description = models.TextField('Description')
    resource_type = models.CharField('Type de ressource', max_length=100, blank=True)
    resource_id = models.CharField('ID ressource', max_length=100, blank=True)
    resource_name = models.CharField('Nom ressource', max_length=200, blank=True)
    
    ip_address = models.GenericIPAddressField('Adresse IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    metadata = models.JSONField('Métadonnées', default=dict)
    
    success = models.BooleanField('Succès', default=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
        verbose_name = 'Activité utilisateur'
        verbose_name_plural = 'Activités utilisateur'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['severity']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} - {self.created_at}"
