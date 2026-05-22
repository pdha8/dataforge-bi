# apps/etl_engine/models.py
"""
Modèles avancés pour l'application etl_engine - Pipeline ETL professionnel
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

from apps.core.models import BaseModel, SoftDeleteModel
from apps.users.models import User
from apps.data_sources.models import DataSource
from apps.data_sources.constants import REFRESH_CHOICES

from .constants import (
    PIPELINE_TYPES, PIPELINE_STATUS, EXECUTION_STATUS,
    TRANSFORMATION_TYPES, ERROR_STRATEGIES, PROCESSING_MODES,
    LOG_LEVELS, NOTIFICATION_TYPES, ENDPOINT_TYPES
)
from .validators import (
    validate_cron_expression, validate_python_code,
    validate_sql_code, validate_transformation_config,
    validate_dependency_graph, validate_retry_policy
)
from .managers import ETLPipelineManager, ExecutionLogManager


# ============================================================================
# PIPELINE ETL PRINCIPAL
# ============================================================================

class ETLPipeline(SoftDeleteModel):
    """
    Pipeline ETL principal - Orchestration des transformations de données
    Hérite de SoftDeleteModel pour la suppression logique
    """
    
    # ========================================================================
    # IDENTITÉ
    # ========================================================================
    name = models.CharField('Nom', max_length=200, db_index=True)
    description = models.TextField('Description', blank=True)
    pipeline_type = models.CharField(
        'Type de pipeline',
        max_length=20,
        choices=PIPELINE_TYPES,
        default='etl',
        db_index=True
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=PIPELINE_STATUS,
        default='draft',
        db_index=True
    )
    version = models.CharField('Version', max_length=20, default='1.0', blank=True)
    
    # ========================================================================
    # SOURCES ET CIBLES
    # ========================================================================
    source = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etl_source_pipelines',
        verbose_name='Source de données'
    )
    source_endpoint_type = models.CharField(
        'Type de source',
        max_length=20,
        choices=ENDPOINT_TYPES,
        default='database'
    )
    source_config = models.JSONField('Configuration source', default=dict, blank=True)
    
    target = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etl_target_pipelines',
        verbose_name='Cible de données'
    )
    target_endpoint_type = models.CharField(
        'Type de cible',
        max_length=20,
        choices=ENDPOINT_TYPES,
        default='database'
    )
    target_config = models.JSONField('Configuration cible', default=dict, blank=True)
    
    # ========================================================================
    # TRANSFORMATIONS
    # ========================================================================
    transformations = models.JSONField(
        'Transformations',
        default=list,
        blank=True,
        help_text="Liste des transformations à appliquer"
    )
    transformation_order = models.JSONField(
        'Ordre des transformations',
        default=list,
        blank=True,
        help_text="Ordre d'exécution des transformations"
    )
    
    # ========================================================================
    # PLANIFICATION
    # ========================================================================
    schedule_enabled = models.BooleanField('Planification activée', default=False)
    schedule_frequency = models.CharField(
        'Fréquence',
        max_length=20,
        choices=REFRESH_CHOICES,
        default='manual',
        blank=True
    )
    schedule_cron = models.CharField(
        'Expression CRON',
        max_length=100,
        blank=True,
        validators=[validate_cron_expression],
        help_text="Expression CRON pour la planification personnalisée"
    )
    last_execution = models.DateTimeField('Dernière exécution', null=True, blank=True)
    next_execution = models.DateTimeField('Prochaine exécution', null=True, blank=True)
    
    # ========================================================================
    # PARAMÈTRES D'EXÉCUTION
    # ========================================================================
    batch_size = models.IntegerField(
        'Taille de lot',
        default=10000,
        validators=[MinValueValidator(1), MaxValueValidator(1000000)]
    )
    timeout_seconds = models.IntegerField(
        'Timeout (secondes)',
        default=3600,
        validators=[MinValueValidator(10), MaxValueValidator(86400)]
    )
    max_errors = models.IntegerField(
        'Erreurs max',
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    error_strategy = models.CharField(
        'Stratégie d\'erreur',
        max_length=20,
        choices=ERROR_STRATEGIES,
        default='fail'
    )
    processing_mode = models.CharField(
        'Mode de traitement',
        max_length=20,
        choices=PROCESSING_MODES,
        default='batch'
    )
    
    # ========================================================================
    # POLITIQUE DE RÉESSAI
    # ========================================================================
    retry_policy = models.JSONField(
        'Politique de réessai',
        default=dict,
        blank=True,
        validators=[validate_retry_policy],
        help_text="Configuration des réessais automatiques"
    )
    
    # ========================================================================
    # DÉPENDANCES
    # ========================================================================
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependents',
        verbose_name='Dépendances'
    )
    dependency_graph = models.JSONField(
        'Graphe de dépendances',
        default=dict,
        blank=True,
        validators=[validate_dependency_graph]
    )
    
    # ========================================================================
    # NOTIFICATIONS
    # ========================================================================
    notifications_enabled = models.BooleanField('Notifications activées', default=False)
    notification_channels = models.JSONField(
        'Canaux de notification',
        default=list,
        blank=True,
        help_text="Liste des canaux pour les notifications"
    )
    notify_on_success = models.BooleanField('Notifier en cas de succès', default=False)
    notify_on_failure = models.BooleanField('Notifier en cas d\'échec', default=True)
    notify_on_start = models.BooleanField('Notifier au démarrage', default=False)
    
    # ========================================================================
    # MÉTRIQUES ET PERFORMANCE
    # ========================================================================
    execution_count = models.IntegerField('Nombre d\'exécutions', default=0)
    success_count = models.IntegerField('Succès', default=0)
    failure_count = models.IntegerField('Échecs', default=0)
    avg_duration_seconds = models.FloatField('Durée moyenne (s)', default=0)
    last_duration_seconds = models.FloatField('Dernière durée (s)', null=True, blank=True)
    total_rows_processed = models.BigIntegerField('Lignes traitées', default=0)
    
    # ========================================================================
    # QUALITÉ DES DONNÉES
    # ========================================================================
    data_quality_score = models.IntegerField(
        'Score de qualité',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    validation_rules = models.JSONField(
        'Règles de validation',
        default=list,
        blank=True,
        help_text="Règles de validation des données"
    )
    
    # ========================================================================
    # MÉTADONNÉES
    # ========================================================================
    tags = models.JSONField('Tags', default=list, blank=True)
    category = models.CharField('Catégorie', max_length=100, blank=True, db_index=True)
    priority = models.IntegerField(
        'Priorité',
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1 = Plus haute priorité, 10 = Plus basse priorité"
    )
    
    # ========================================================================
    # PROPRIÉTAIRES
    # ========================================================================
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_etl_pipelines',
        verbose_name='Propriétaire'
    )
    team = models.ForeignKey(
        'users.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etl_pipelines',
        verbose_name='Équipe'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_etl_pipelines',
        verbose_name='Créé par'
    )
    
    notes = models.TextField('Notes', blank=True)
    
    # Gestionnaire personnalisé
    objects = ETLPipelineManager()
    
    class Meta:
        db_table = 'etl_pipelines'
        ordering = ['-priority', 'name']
        verbose_name = 'Pipeline ETL'
        verbose_name_plural = 'Pipelines ETL'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['pipeline_type', 'status']),
            models.Index(fields=['category', 'priority']),
            models.Index(fields=['owner', 'team']),
            models.Index(fields=['-last_execution']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_pipeline_type_display()})"
    
    # ========================================================================
    # PROPRIÉTÉS UTILES
    # ========================================================================
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def success_rate(self):
        if self.execution_count == 0:
            return 100.0
        return (self.success_count / self.execution_count) * 100
    
    @property
    def needs_execution(self):
        if not self.schedule_enabled or self.status != 'active':
            return False
        if not self.next_execution:
            return True
        return timezone.now() >= self.next_execution
    
    @property
    def health_status(self):
        if self.status == 'error':
            return 'critical'
        elif self.failure_count > self.success_count:
            return 'warning'
        elif self.data_quality_score < 50:
            return 'poor'
        elif self.data_quality_score < 75:
            return 'fair'
        return 'good'
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    def calculate_next_execution(self):
        """Calcule la prochaine exécution"""
        if not self.schedule_enabled:
            return
        
        now = timezone.now()
        if self.schedule_cron:
            # À implémenter avec croniter
            pass
        else:
            freq_map = {
                'realtime': timedelta(seconds=10),
                'every_5m': timedelta(minutes=5),
                'every_15m': timedelta(minutes=15),
                'every_30m': timedelta(minutes=30),
                'hourly': timedelta(hours=1),
                'every_6h': timedelta(hours=6),
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30),
            }
            delta = freq_map.get(self.schedule_frequency)
            if delta:
                self.next_execution = now + delta
    
    def update_metrics(self, duration_seconds, rows_processed, success=True):
        """Met à jour les métriques du pipeline"""
        self.execution_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        self.total_rows_processed += rows_processed
        self.last_duration_seconds = duration_seconds
        
        # Calculer la moyenne glissante
        total_time = self.avg_duration_seconds * (self.execution_count - 1)
        self.avg_duration_seconds = (total_time + duration_seconds) / self.execution_count
        
        self.last_execution = timezone.now()
        self.calculate_next_execution()
        
        self.save(update_fields=[
            'execution_count', 'success_count', 'failure_count',
            'total_rows_processed', 'last_duration_seconds',
            'avg_duration_seconds', 'last_execution', 'next_execution'
        ])
    
    def log_error(self, error_message, step_name=None):
        """Enregistre une erreur"""
        self.status = 'error'
        self.save(update_fields=['status'])
        
        ExecutionLog.objects.create(
            pipeline=self,
            status='failed',
            error_message=error_message[:2000],
            step_name=step_name
        )
    
    def calculate_quality_score(self):
        """Calcule le score de qualité"""
        score = 100
        
        # Pénalités pour échecs
        if self.execution_count > 0:
            failure_rate = (self.failure_count / self.execution_count) * 100
            score -= min(failure_rate, 50)
        
        # Pénalités pour données non traitées
        if self.total_rows_processed == 0 and self.execution_count > 0:
            score -= 20
        
        self.data_quality_score = max(score, 0)
        self.save(update_fields=['data_quality_score'])
        return self.data_quality_score


# ============================================================================
# TRANSFORMATIONS
# ============================================================================

class Transformation(BaseModel):
    """
    Transformation individuelle dans un pipeline ETL
    """
    pipeline = models.ForeignKey(
        ETLPipeline,
        on_delete=models.CASCADE,
        related_name='transformation_list',
        verbose_name='Pipeline'
    )
    order = models.IntegerField('Ordre', default=0)
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    transformation_type = models.CharField(
        'Type de transformation',
        max_length=30,
        choices=TRANSFORMATION_TYPES
    )
    
    # Configuration
    config = models.JSONField(
        'Configuration',
        default=dict,
        blank=True,
        validators=[validate_transformation_config]
    )
    
    # Code personnalisé
    custom_code = models.TextField(
        'Code personnalisé',
        blank=True,
        validators=[validate_python_code],
        help_text="Code Python pour les transformations personnalisées"
    )
    sql_code = models.TextField(
        'Code SQL',
        blank=True,
        validators=[validate_sql_code],
        help_text="Code SQL pour les transformations SQL"
    )
    
    # Métadonnées
    is_enabled = models.BooleanField('Activée', default=True)
    is_critical = models.BooleanField('Critique', default=False,
                                      help_text="Si échoue, arrête tout le pipeline")
    
    # Métriques
    execution_count = models.IntegerField('Nombre d\'exécutions', default=0)
    avg_duration_ms = models.FloatField('Durée moyenne (ms)', default=0)
    last_duration_ms = models.FloatField('Dernière durée (ms)', null=True, blank=True)
    error_count = models.IntegerField('Nombre d\'erreurs', default=0)
    last_error = models.TextField('Dernière erreur', blank=True)
    
    class Meta:
        db_table = 'etl_transformations'
        ordering = ['pipeline', 'order']
        unique_together = ['pipeline', 'order']
        verbose_name = 'Transformation'
        verbose_name_plural = 'Transformations'
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.name} (étape {self.order})"
    
    def move_up(self):
        previous = Transformation.objects.filter(
            pipeline=self.pipeline, order__lt=self.order
        ).order_by('-order').first()
        if previous:
            previous.order, self.order = self.order, previous.order
            previous.save(update_fields=['order'])
            self.save(update_fields=['order'])

    def move_down(self):
        next_t = Transformation.objects.filter(
            pipeline=self.pipeline, order__gt=self.order
        ).order_by('order').first()
        if next_t:
            next_t.order, self.order = self.order, next_t.order
            next_t.save(update_fields=['order'])
            self.save(update_fields=['order'])

    def update_metrics(self, duration_ms, success=True):
        """Met à jour les métriques de la transformation"""
        self.execution_count += 1
        self.last_duration_ms = duration_ms

        total_time = self.avg_duration_ms * (self.execution_count - 1)
        self.avg_duration_ms = (total_time + duration_ms) / self.execution_count

        if not success:
            self.error_count += 1

        self.save(update_fields=[
            'execution_count', 'last_duration_ms', 'avg_duration_ms', 'error_count'
        ])


# ============================================================================
# EXÉCUTIONS
# ============================================================================

class ExecutionLog(BaseModel):
    """
    Journal des exécutions de pipeline
    """
    pipeline = models.ForeignKey(
        ETLPipeline,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='Pipeline'
    )
    execution_id = models.CharField(
        'ID d\'exécution',
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Identifiant unique de l'exécution"
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=EXECUTION_STATUS,
        default='pending',
        db_index=True
    )
    
    # Horodatage
    started_at = models.DateTimeField('Début', auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField('Fin', null=True, blank=True)
    duration_seconds = models.FloatField('Durée (secondes)', null=True, blank=True)
    
    # Métriques
    rows_read = models.BigIntegerField('Lignes lues', default=0)
    rows_written = models.BigIntegerField('Lignes écrites', default=0)
    rows_errors = models.BigIntegerField('Lignes en erreur', default=0)
    
    # Détails
    triggered_by = models.CharField(
        'Déclenché par',
        max_length=50,
        default='manual',
        choices=[
            ('manual', '👤 Manuel'),
            ('schedule', '⏰ Planification'),
            ('api', '🌐 API'),
            ('dependency', '🔗 Dépendance'),
            ('retry', '🔄 Réessai'),
        ]
    )
    triggered_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_executions',
        verbose_name='Déclenché par'
    )
    
    # Résultats
    result_summary = models.JSONField('Résumé des résultats', default=dict, blank=True)
    error_message = models.TextField('Message d\'erreur', blank=True)
    error_traceback = models.TextField('Trace d\'erreur', blank=True)
    
    # Métadonnées
    execution_metadata = models.JSONField('Métadonnées d\'exécution', default=dict, blank=True)
    transformation_logs = models.JSONField('Logs des transformations', default=list, blank=True)
    
    objects = ExecutionLogManager()
    
    class Meta:
        db_table = 'etl_execution_logs'
        ordering = ['-started_at']
        verbose_name = 'Journal d\'exécution'
        verbose_name_plural = 'Journaux d\'exécution'
        indexes = [
            models.Index(fields=['pipeline', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['triggered_by']),
            models.Index(fields=['execution_id']),
        ]
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.execution_id} ({self.status})"
    
    def complete(self, success=True):
        """Marque l'exécution comme terminée"""
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.status = 'completed' if success else 'failed'
        self.save()
    
    def add_transformation_log(self, transformation_name, status, details=None):
        """Ajoute un log de transformation"""
        log_entry = {
            'transformation': transformation_name,
            'status': status,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        self.transformation_logs.append(log_entry)
        self.save(update_fields=['transformation_logs'])


# ============================================================================
# SCHÉMA DE DESTINATION
# ============================================================================

class TargetSchema(BaseModel):
    """
    Schéma de destination pour les pipelines ETL
    """
    pipeline = models.OneToOneField(
        ETLPipeline,
        on_delete=models.CASCADE,
        related_name='target_schema',
        verbose_name='Pipeline'
    )
    table_name = models.CharField('Nom de la table', max_length=200)
    schema_name = models.CharField('Nom du schéma', max_length=200, blank=True)
    
    # Colonnes
    columns = models.JSONField(
        'Colonnes',
        default=list,
        blank=True,
        help_text="Liste des colonnes avec leurs types"
    )
    primary_key = models.JSONField('Clé primaire', default=list, blank=True)
    indexes = models.JSONField('Index', default=list, blank=True)
    
    # Stratégie d'insertion
    insert_strategy = models.CharField(
        'Stratégie d\'insertion',
        max_length=20,
        default='append',
        choices=[
            ('append', '➕ Append'),
            ('upsert', '🔄 Upsert'),
            ('merge', '🔀 Merge'),
            ('replace', '🗑️ Replace'),
            ('truncate_insert', '📝 Truncate & Insert'),
        ]
    )
    upsert_keys = models.JSONField('Clés pour upsert', default=list, blank=True)
    
    # Partitionnement
    is_partitioned = models.BooleanField('Partitionné', default=False)
    partition_column = models.CharField('Colonne de partition', max_length=200, blank=True)
    partition_type = models.CharField(
        'Type de partition',
        max_length=20,
        blank=True,
        choices=[
            ('range', '📊 Range'),
            ('list', '📋 List'),
            ('hash', '#️⃣ Hash'),
        ]
    )
    
    class Meta:
        db_table = 'etl_target_schemas'
        verbose_name = 'Schéma cible'
        verbose_name_plural = 'Schémas cibles'
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.table_name}"


# ============================================================================
# SCHÉMA DE SOURCE
# ============================================================================

class SourceSchema(BaseModel):
    """
    Schéma de source pour les pipelines ETL
    """
    pipeline = models.OneToOneField(
        ETLPipeline,
        on_delete=models.CASCADE,
        related_name='source_schema',
        verbose_name='Pipeline'
    )
    
    # Requête source
    query = models.TextField(
        'Requête SQL',
        blank=True,
        help_text="Requête SQL pour extraire les données"
    )
    table_name = models.CharField('Nom de la table', max_length=200, blank=True)
    
    # Filtres
    filters = models.JSONField(
        'Filtres',
        default=list,
        blank=True,
        help_text="Liste des filtres à appliquer"
    )
    
    # Colonnes sélectionnées
    selected_columns = models.JSONField(
        'Colonnes sélectionnées',
        default=list,
        blank=True,
        help_text="Liste des colonnes à extraire (vide = toutes)"
    )
    
    # Incremental loading
    incremental_column = models.CharField(
        'Colonne incrémentale',
        max_length=200,
        blank=True,
        help_text="Colonne utilisée pour le chargement incrémental"
    )
    last_value = models.CharField(
        'Dernière valeur',
        max_length=500,
        blank=True,
        help_text="Dernière valeur extraite pour l'incrémental"
    )
    
    class Meta:
        db_table = 'etl_source_schemas'
        verbose_name = 'Schéma source'
        verbose_name_plural = 'Schémas sources'
    
    def __str__(self):
        return f"{self.pipeline.name} - Source"


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class PipelineNotification(BaseModel):
    """
    Notification de pipeline
    """
    pipeline = models.ForeignKey(
        ETLPipeline,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Pipeline'
    )
    channel = models.CharField(
        'Canal',
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    recipient = models.CharField('Destinataire', max_length=500)
    config = models.JSONField('Configuration', default=dict, blank=True)
    
    # Conditions
    send_on_start = models.BooleanField('Envoyer au démarrage', default=False)
    send_on_success = models.BooleanField('Envoyer en cas de succès', default=False)
    send_on_failure = models.BooleanField('Envoyer en cas d\'échec', default=True)
    
    is_enabled = models.BooleanField('Activée', default=True)
    
    class Meta:
        db_table = 'etl_pipeline_notifications'
        verbose_name = 'Notification de pipeline'
        verbose_name_plural = 'Notifications de pipeline'
    
    def __str__(self):
        return f"{self.pipeline.name} - {self.get_channel_display()}"
