# apps/visualizations/models.py
"""
Visualizations Models - Tableaux de bord BI avancés avec rendu optimisé
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.core.models import BaseModel, SoftDeleteModel
from apps.users.models import User
from apps.star_schema.models import DimensionalSchema
from apps.data_warehouse.models import Measure

from .constants import (
    DASHBOARD_TYPES, REFRESH_FREQUENCIES,
    EXPORT_FORMATS, STATUS_CHOICES, ACCESS_LEVELS,
    THEMES, WIDGET_TYPES, KPI_TYPES, TREND_DIRECTIONS
)
from .validators import (
    validate_chart_config, validate_dashboard_layout,
    validate_kpi_config, validate_filter_expression
)
from .managers import (
    DashboardManager, ReportManager,
    KpiManager, WidgetManager, FavoriteManager
)


# ============================================================================
# TABLEAU DE BORD PRINCIPAL
# ============================================================================

class Dashboard(BaseModel):
    """
    Tableau de bord BI avancé avec support multi-pages et widgets dynamiques
    """
    
    # Informations de base
    name = models.CharField(
        'Nom du tableau de bord',
        max_length=200,
        db_index=True,
        help_text="Nom unique du tableau de bord"
    )
    slug = models.SlugField(
        'Slug',
        max_length=200,
        unique=True,
        help_text="Identifiant unique pour l'URL"
    )
    description = models.TextField('Description', blank=True)
    dashboard_type = models.CharField(
        'Type',
        max_length=20,
        choices=DASHBOARD_TYPES,
        default='analytical'
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    
    # Layout et design
    layout = models.JSONField(
        'Layout',
        default=dict,
        validators=[validate_dashboard_layout],
        help_text="Configuration GridStack du layout"
    )
    theme = models.CharField(
        'Thème',
        max_length=20,
        choices=THEMES,
        default='light'
    )
    custom_css = models.TextField('CSS personnalisé', blank=True)
    custom_js = models.TextField('JavaScript personnalisé', blank=True)
    
    # Configuration d'affichage
    is_fullscreen = models.BooleanField('Mode plein écran', default=False)
    show_toolbar = models.BooleanField('Afficher la barre d\'outils', default=True)
    show_filters = models.BooleanField('Afficher les filtres', default=True)
    
    # Filtres globaux
    global_filters = models.JSONField(
        'Filtres globaux',
        default=list,
        blank=True,
        validators=[validate_filter_expression],
        help_text="Filtres appliqués à tous les widgets"
    )
    
    # Paramètres de rafraîchissement
    refresh_frequency = models.CharField(
        'Fréquence de rafraîchissement',
        max_length=20,
        choices=REFRESH_FREQUENCIES,
        default='manual'
    )
    auto_refresh = models.BooleanField('Auto rafraîchissement', default=False)
    last_refresh = models.DateTimeField('Dernier rafraîchissement', null=True, blank=True)
    next_refresh = models.DateTimeField('Prochain rafraîchissement', null=True, blank=True)
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    category = models.CharField('Catégorie', max_length=100, blank=True, db_index=True)
    thumbnail = models.ImageField(
        'Miniature',
        upload_to='dashboards/thumbnails/%Y/%m/',
        blank=True,
        help_text="Aperçu du tableau de bord"
    )
    
    # Accès et permissions
    access_level = models.CharField(
        'Niveau d\'accès',
        max_length=20,
        choices=ACCESS_LEVELS,
        default='private'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_dashboards',
        verbose_name='Propriétaire'
    )
    team = models.ForeignKey(
        'users.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dashboards',
        verbose_name='Équipe'
    )
    allowed_users = models.ManyToManyField(
        User,
        related_name='shared_dashboards',
        blank=True,
        verbose_name='Utilisateurs autorisés'
    )
    
    # Statistiques d'utilisation
    view_count = models.IntegerField('Nombre de vues', default=0)
    favorite_count = models.IntegerField('Nombre de favoris', default=0)
    last_viewed = models.DateTimeField('Dernière vue', null=True, blank=True)
    avg_load_time_ms = models.FloatField('Temps de chargement moyen (ms)', default=0)
    
    # Export
    allow_export = models.BooleanField('Autoriser l\'export', default=True)
    default_export_format = models.CharField(
        'Format d\'export par défaut',
        max_length=20,
        choices=EXPORT_FORMATS,
        default='pdf'
    )
    
    # Versioning
    version = models.IntegerField('Version', default=1)
    version_notes = models.TextField('Notes de version', blank=True)
    published_at = models.DateTimeField('Publié le', null=True, blank=True)
    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='published_dashboards',
        verbose_name='Publié par'
    )
    
    # Gestionnaire
    objects = DashboardManager()
    
    class Meta:
        db_table = 'dashboards'
        ordering = ['-view_count', 'name']
        verbose_name = 'Tableau de bord'
        verbose_name_plural = 'Tableaux de bord'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['dashboard_type', 'status']),
            models.Index(fields=['owner', 'team']),
            models.Index(fields=['category']),
            models.Index(fields=['-view_count']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_dashboard_type_display()})"
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    @property
    def widget_count(self):
        return self.widgets.count()
    
    @property
    def chart_count(self):
        return self.widgets.filter(widget_type='chart').count()
    
    @property
    def kpi_count(self):
        return self.widgets.filter(widget_type='kpi').count()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def increment_view(self):
        """Incrémente le compteur de vues"""
        self.view_count += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed'])
    
    def duplicate(self, user=None):
        """Duplique le tableau de bord"""
        new_dashboard = Dashboard.objects.create(
            name=f"{self.name} (Copie)",
            description=self.description,
            dashboard_type=self.dashboard_type,
            status='draft',
            layout=self.layout,
            theme=self.theme,
            global_filters=self.global_filters,
            owner=user or self.owner,
            access_level='private'
        )
        
        # Copier les widgets
        for widget in self.widgets.all():
            widget.duplicate(new_dashboard)
        
        return new_dashboard


# ============================================================================
# WIDGET - Élément de tableau de bord
# ============================================================================

class Widget(BaseModel):
    """
    Widget réutilisable pour les tableaux de bord
    Supporte graphiques, KPIs, tableaux, textes, etc.
    """
    
    # Informations de base
    name = models.CharField('Nom du widget', max_length=200)
    description = models.TextField('Description', blank=True)
    widget_type = models.CharField(
        'Type de widget',
        max_length=20,
        choices=WIDGET_TYPES,
        default='chart'
    )
    
    # Dashboard parent
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name='Tableau de bord'
    )
    
    # Données source
    dimensional_schema = models.ForeignKey(
        DimensionalSchema,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='widgets',
        verbose_name='Schéma dimensionnel'
    )
    
    # Configuration selon le type
    config = models.JSONField(
        'Configuration',
        default=dict,
        validators=[validate_chart_config],
        help_text="Configuration spécifique au type de widget"
    )
    
    # Position et taille
    position = models.JSONField(
        'Position',
        default=dict,
        help_text="Position dans la grille (x, y, w, h)"
    )
    
    # Filtres spécifiques
    filters = models.JSONField(
        'Filtres',
        default=list,
        blank=True,
        validators=[validate_filter_expression],
        help_text="Filtres spécifiques au widget"
    )
    
    # Style
    style = models.JSONField(
        'Style',
        default=dict,
        blank=True,
        help_text="Style CSS personnalisé"
    )
    
    # Interactivité
    drilldown_enabled = models.BooleanField('Drilldown activé', default=False)
    drilldown_config = models.JSONField('Configuration drilldown', default=dict, blank=True)
    
    # Cache
    cache_enabled = models.BooleanField('Cache activé', default=True)
    cache_ttl_seconds = models.IntegerField('TTL cache (secondes)', default=300)
    cached_data = models.JSONField('Données en cache', default=dict, blank=True)
    cached_at = models.DateTimeField('Mis en cache le', null=True, blank=True)
    
    # Métadonnées
    is_enabled = models.BooleanField('Activé', default=True)
    refresh_on_load = models.BooleanField('Rafraîchir au chargement', default=True)
    order = models.IntegerField('Ordre', default=0)
    
    # Statistiques
    render_count = models.IntegerField('Nombre de rendus', default=0)
    avg_render_time_ms = models.FloatField('Temps de rendu moyen (ms)', default=0)
    last_rendered = models.DateTimeField('Dernier rendu', null=True, blank=True)
    
    # Gestionnaire
    objects = WidgetManager()
    
    class Meta:
        db_table = 'widgets'
        ordering = ['dashboard', 'order']
        verbose_name = 'Widget'
        verbose_name_plural = 'Widgets'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['widget_type']),
            models.Index(fields=['dashboard', 'is_enabled']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"
    
    def get_data(self, filters=None):
        """
        Récupère les données du widget
        """
        if self.cache_enabled and self.cached_data and self._is_cache_valid():
            return self.cached_data
        
        data = self._fetch_data(filters)
        
        if self.cache_enabled:
            self.cached_data = data
            self.cached_at = timezone.now()
            self.save(update_fields=['cached_data', 'cached_at'])
        
        return data
    
    def _is_cache_valid(self):
        """Vérifie si le cache est valide"""
        if not self.cached_at:
            return False
        delta = timezone.now() - self.cached_at
        return delta.total_seconds() < self.cache_ttl_seconds
    
    def _fetch_data(self, filters=None):
        """Récupère les données depuis la source"""
        from .services import WidgetDataService
        service = WidgetDataService(self)
        return service.fetch_data(filters)
    
    def render(self, data=None):
        """
        Rendu du widget pour le frontend
        """
        from .services import WidgetRenderService
        service = WidgetRenderService(self)
        return service.render(data)
    
    def duplicate(self, new_dashboard):
        """Duplique le widget"""
        return Widget.objects.create(
            name=f"{self.name} (Copie)",
            description=self.description,
            widget_type=self.widget_type,
            dashboard=new_dashboard,
            dimensional_schema=self.dimensional_schema,
            config=self.config,
            position=self.position,
            filters=self.filters,
            style=self.style,
            order=self.order
        )


# ============================================================================
# KPI - Indicateur de performance
# ============================================================================

class KPI(BaseModel):
    """
    Indicateur de performance clé (KPI)
    """
    
    # Informations de base
    name = models.CharField('Nom du KPI', max_length=200)
    description = models.TextField('Description', blank=True)
    kpi_type = models.CharField(
        'Type',
        max_length=20,
        choices=KPI_TYPES,
        default='number'
    )
    
    # Source de données
    dimensional_schema = models.ForeignKey(
        DimensionalSchema,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kpis',
        verbose_name='Schéma dimensionnel'
    )
    measure = models.ForeignKey(
        Measure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kpis',
        verbose_name='Mesure associée'
    )
    
    # Configuration
    config = models.JSONField(
        'Configuration',
        default=dict,
        validators=[validate_kpi_config],
        help_text="Configuration du KPI"
    )
    
    # Formules et calculs
    formula = models.TextField(
        'Formule',
        blank=True,
        help_text="Formule de calcul personnalisée"
    )
    aggregation = models.CharField(
        'Agrégation',
        max_length=20,
        default='sum',
        help_text="Type d'agrégation"
    )
    
    # Filtres
    filters = models.JSONField(
        'Filtres',
        default=list,
        blank=True,
        validators=[validate_filter_expression]
    )
    
    # Cibles et seuils
    target_value = models.FloatField('Valeur cible', null=True, blank=True)
    warning_threshold = models.FloatField('Seuil d\'avertissement', null=True, blank=True)
    critical_threshold = models.FloatField('Seuil critique', null=True, blank=True)
    
    # Formatage
    format_string = models.CharField('Format d\'affichage', max_length=50, blank=True)
    unit = models.CharField('Unité', max_length=50, blank=True)
    decimal_places = models.IntegerField('Décimales', default=2)
    
    # Tendances
    track_trend = models.BooleanField('Suivre la tendance', default=True)
    trend_direction = models.CharField(
        'Direction de tendance',
        max_length=20,
        choices=TREND_DIRECTIONS,
        blank=True
    )
    trend_period = models.CharField('Période de comparaison', max_length=20, default='previous_period')
    
    # Dashboard parent
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='kpis',
        verbose_name='Tableau de bord',
        null=True,
        blank=True
    )
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    order = models.IntegerField('Ordre', default=0)
    
    # Valeurs calculées
    current_value = models.FloatField('Valeur actuelle', null=True, blank=True)
    previous_value = models.FloatField('Valeur précédente', null=True, blank=True)
    trend_percentage = models.FloatField('Pourcentage de tendance', null=True, blank=True)
    last_calculated = models.DateTimeField('Dernier calcul', null=True, blank=True)
    
    # Gestionnaire
    objects = KpiManager()
    
    class Meta:
        db_table = 'kpis'
        ordering = ['order', 'name']
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['kpi_type']),
            models.Index(fields=['dashboard']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_kpi_type_display()})"
    
    def calculate(self, filters=None):
        """
        Calcule la valeur du KPI
        """
        from .services import KPIService
        service = KPIService(self)
        return service.calculate(filters)
    
    def get_status(self):
        """
        Retourne le statut du KPI basé sur les seuils
        """
        if self.current_value is None:
            return 'unknown'
        
        if self.critical_threshold is not None:
            if self.kpi_type == 'percentage' and self.trend_direction == 'up':
                if self.current_value <= self.critical_threshold:
                    return 'critical'
            elif self.current_value >= self.critical_threshold:
                return 'critical'
        
        if self.warning_threshold is not None:
            if self.current_value >= self.warning_threshold:
                return 'warning'
        
        return 'success'
    
    def get_status_color(self):
        """
        Retourne la couleur du statut
        """
        colors = {
            'success': '#28a745',
            'warning': '#ffc107',
            'critical': '#dc3545',
            'unknown': '#6c757d'
        }
        return colors.get(self.get_status(), '#6c757d')
    
    def get_status_icon(self):
        """
        Retourne l'icône du statut
        """
        icons = {
            'success': '✅',
            'warning': '⚠️',
            'critical': '🔴',
            'unknown': '❓'
        }
        return icons.get(self.get_status(), '❓')


# ============================================================================
# RAPPORT PROGRAMMÉ
# ============================================================================

class Report(BaseModel):
    """
    Rapport généré périodiquement à partir des tableaux de bord
    """
    
    name = models.CharField('Nom du rapport', max_length=200)
    description = models.TextField('Description', blank=True)
    
    # Source
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Tableau de bord source'
    )
    
    # Configuration
    format = models.CharField(
        'Format',
        max_length=20,
        choices=EXPORT_FORMATS,
        default='pdf'
    )
    schedule = models.CharField(
        'Planification CRON',
        max_length=100,
        blank=True,
        help_text="Expression CRON (ex: '0 9 * * *' pour tous les jours à 9h)"
    )
    recipients = models.JSONField(
        'Destinataires',
        default=list,
        help_text="Liste des adresses email"
    )
    
    # Filtres
    filters = models.JSONField(
        'Filtres',
        default=dict,
        blank=True,
        help_text="Filtres appliqués lors de la génération"
    )
    
    # Options
    include_metadata = models.BooleanField('Inclure les métadonnées', default=True)
    include_filters = models.BooleanField('Inclure les filtres', default=True)
    page_size = models.CharField('Format de page', max_length=20, default='A4')
    orientation = models.CharField('Orientation', max_length=10, default='portrait')
    
    # Génération
    last_generated = models.DateTimeField('Dernière génération', null=True, blank=True)
    last_generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name='Généré par'
    )
    generation_count = models.IntegerField('Nombre de générations', default=0)
    last_error = models.TextField('Dernière erreur', blank=True)
    
    # Métadonnées
    is_active = models.BooleanField('Actif', default=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_reports',
        verbose_name='Propriétaire'
    )
    tags = models.JSONField('Tags', default=list, blank=True)
    
    # Gestionnaire
    objects = ReportManager()
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        verbose_name = 'Rapport'
        verbose_name_plural = 'Rapports'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['dashboard']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-last_generated']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.format.upper()})"
    
    def generate(self, user=None):
        """
        Génère le rapport
        """
        from .services import ReportGenerationService
        service = ReportGenerationService(self)
        return service.generate(user)
    
    def get_next_run(self):
        """
        Calcule la prochaine exécution
        """
        from croniter import croniter
        from datetime import datetime
        
        if not self.schedule:
            return None
        
        cron = croniter(self.schedule, datetime.now())
        return cron.get_next(datetime)


# ============================================================================
# FAVORI
# ============================================================================

class Favorite(BaseModel):
    """
    Favoris utilisateur
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Utilisateur'
    )
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='favorited_by',
        verbose_name='Tableau de bord'
    )
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='favorited_by',
        verbose_name='KPI'
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='favorited_by',
        verbose_name='Rapport'
    )
    order = models.IntegerField('Ordre', default=0)
    notes = models.TextField('Notes', blank=True)
    
    # Gestionnaire
    objects = FavoriteManager()
    
    class Meta:
        db_table = 'favorites'
        ordering = ['user', 'order']
        verbose_name = 'Favori'
        verbose_name_plural = 'Favoris'
        unique_together = ['user', 'dashboard', 'kpi', 'report']
        indexes = [
            models.Index(fields=['user', 'dashboard']),
            models.Index(fields=['user', 'kpi']),
            models.Index(fields=['user', 'report']),
        ]
    
    def __str__(self):
        if self.dashboard:
            return f"{self.user.email} - {self.dashboard.name}"
        elif self.kpi:
            return f"{self.user.email} - {self.kpi.name}"
        elif self.report:
            return f"{self.user.email} - {self.report.name}"
        return f"{self.user.email} - Favori"


# ============================================================================
# ACTIVITÉ DE VISUALISATION
# ============================================================================

class VisualizationActivity(BaseModel):
    """
    Journal des activités de visualisation
    """
    
    ACTIVITY_TYPES = [
        ('view', '👁️ Vue'),
        ('export', '📤 Export'),
        ('share', '🔗 Partage'),
        ('edit', '✏️ Édition'),
        ('favorite', '⭐ Favori'),
        ('comment', '💬 Commentaire'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='visualization_activities',
        verbose_name='Utilisateur'
    )
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name='Tableau de bord'
    )
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name='Widget'
    )
    activity_type = models.CharField(
        'Type d\'activité',
        max_length=20,
        choices=ACTIVITY_TYPES,
        db_index=True
    )
    description = models.TextField('Description')
    metadata = models.JSONField('Métadonnées', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('Adresse IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    
    class Meta:
        db_table = 'visualization_activities'
        ordering = ['-created_at']
        verbose_name = 'Activité de visualisation'
        verbose_name_plural = 'Activités de visualisation'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['dashboard', '-created_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.activity_type} - {self.created_at}"
