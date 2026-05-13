# apps/data_sources/models.py
"""
Data Sources Models - Version Optimisée pour Sotifibre BI
Combine le meilleur des 3 versions avec des fonctionnalités BI avancées
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from datetime import timedelta
import hashlib

from apps.core.models import BaseModel, SoftDeleteModel
from apps.users.models import User

# Importer depuis constants.py directement
from .constants import (
    SOURCE_TYPE_CHOICES,
    STATUS_CHOICES,
    FILE_PROCESS_STATUS,
    LOG_LEVEL_CHOICES,
    QUERY_STEP_TYPES,
    DATABASE_TYPES,
    API_TYPES,
    FILE_TYPES,
    AUTH_TYPES,
    SYNC_FREQUENCIES,
    QUERY_TYPES,
)

from .validators import (
    validate_connection_string, validate_hostname, validate_port,
    validate_sql_query, validate_table_name, validate_column_name
)
from .managers import (
    DataSourceManager, DataTableManager, DataQueryManager,
    DataSourceLogManager, DataSourceMetricManager
)


# ============================================================================
# SOURCES DE DONNÉES - VERSION AVANCÉE
# ============================================================================

class DataSource(SoftDeleteModel):
    """
    Source de données BI - Version complète avec 25+ types de sources
    Hérite de SoftDeleteModel pour la suppression logique
    """
    
    # ========================================================================
    # IDENTITÉ
    # ========================================================================
    name = models.CharField('Nom', max_length=200, db_index=True)
    description = models.TextField('Description', blank=True)
    source_type = models.CharField('Type de source', max_length=50, choices=SOURCE_TYPE_CHOICES, db_index=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    version = models.CharField('Version', max_length=20, default='1.0', blank=True)
    
    # ========================================================================
    # CONNEXION
    # ========================================================================
    connection_string = models.TextField('Chaîne de connexion', blank=True, validators=[validate_connection_string])
    connection_details = models.JSONField('Détails de connexion', default=dict, blank=True)
    
    # Base de données
    database_type = models.CharField('Type de base', max_length=30, choices=DATABASE_TYPES, blank=True, null=True)
    host = models.CharField('Hôte', max_length=255, blank=True, validators=[validate_hostname])
    port = models.IntegerField('Port', blank=True, null=True, validators=[validate_port])
    database_name = models.CharField('Nom de la base', max_length=200, blank=True)
    schema_name = models.CharField('Schéma', max_length=200, blank=True)
    username = models.CharField('Nom d\'utilisateur', max_length=200, blank=True)
    password = models.CharField('Mot de passe', max_length=500, blank=True)
    
    # API
    api_type = models.CharField('Type d\'API', max_length=20, choices=API_TYPES, blank=True, null=True)
    api_url = models.URLField('URL API', blank=True)
    api_endpoint = models.CharField('Endpoint', max_length=500, blank=True)
    api_headers = models.JSONField('Headers API', default=dict, blank=True)
    api_params = models.JSONField('Paramètres API', default=dict, blank=True)
    
    # Fichier
    file_type = models.CharField('Type de fichier', max_length=20, choices=FILE_TYPES, blank=True, null=True)
    file_path = models.CharField('Chemin du fichier', max_length=500, blank=True)
    file_url = models.URLField('URL du fichier', blank=True)
    file_encoding = models.CharField('Encodage', max_length=20, default='utf-8')
    file_delimiter = models.CharField('Délimiteur', max_length=5, default=',')
    
    # Cloud Storage
    cloud_provider = models.CharField('Fournisseur cloud', max_length=50, blank=True)
    bucket_name = models.CharField('Nom du bucket', max_length=200, blank=True)
    object_key = models.CharField('Clé de l\'objet', max_length=500, blank=True)
    region = models.CharField('Région', max_length=50, blank=True)
    
    # Streaming
    streaming_topic = models.CharField('Topic', max_length=200, blank=True)
    streaming_broker = models.CharField('Broker', max_length=200, blank=True)
    
    # Sécurité SSL
    use_ssl = models.BooleanField('Utiliser SSL/TLS', default=True)
    ssl_certificate = models.TextField('Certificat SSL', blank=True)
    ssl_mode = models.CharField('Mode SSL', max_length=50, default='require', blank=True)
    
    # ========================================================================
    # AUTHENTIFICATION
    # ========================================================================
    auth_type = models.CharField('Type d\'authentification', max_length=20, choices=AUTH_TYPES, default='none')
    auth_token = models.CharField('Token', max_length=500, blank=True)
    api_key = models.CharField('API Key', max_length=500, blank=True)
    api_key_header = models.CharField('Header API Key', max_length=100, default='X-API-Key')
    credentials = models.JSONField('Identifiants (chiffrés)', default=dict, blank=True)
    use_credential_vault = models.BooleanField('Utiliser le coffre de mots de passe', default=False)
    
    # OAuth2
    oauth2_client_id = models.CharField('Client ID OAuth2', max_length=200, blank=True)
    oauth2_client_secret = models.CharField('Client Secret OAuth2', max_length=500, blank=True)
    oauth2_token_url = models.URLField('URL token OAuth2', blank=True)
    
    # ========================================================================
    # SYNCHRONISATION ET RAFRAÎCHISSEMENT
    # ========================================================================
    sync_frequency = models.CharField('Fréquence synchronisation', max_length=20, choices=SYNC_FREQUENCIES, default='manual')
    auto_refresh_enabled = models.BooleanField('Auto rafraîchissement', default=False)
    last_sync = models.DateTimeField('Dernière synchronisation', null=True, blank=True)
    next_sync = models.DateTimeField('Prochaine synchronisation', null=True, blank=True)
    last_sync_status = models.CharField('Statut dernière synchro', max_length=200, blank=True)
    last_sync_error = models.TextField('Erreur dernière synchro', blank=True)
    last_sync_duration_ms = models.IntegerField('Durée dernière synchro (ms)', null=True, blank=True)
    refresh_schedule = models.JSONField('Planification personnalisée', default=dict, blank=True)
    
    # ========================================================================
    # QUALITÉ DES DONNÉES
    # ========================================================================
    data_quality_score = models.IntegerField('Score de qualité', default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)])
    row_count = models.BigIntegerField('Nombre de lignes', default=0)
    column_count = models.IntegerField('Nombre de colonnes', default=0)
    data_size_bytes = models.BigIntegerField('Taille des données (octets)', default=0)
    last_profiled_at = models.DateTimeField('Dernier profilage', null=True, blank=True)
    profile_results = models.JSONField('Résultats de profilage', default=dict, blank=True)
    
    # ========================================================================
    # VALIDATION ET TESTS
    # ========================================================================
    is_validated = models.BooleanField('Validé', default=False)
    validation_errors = models.JSONField('Erreurs de validation', default=list, blank=True)
    last_test_date = models.DateTimeField('Dernier test', null=True, blank=True)
    test_results = models.JSONField('Résultats des tests', default=dict, blank=True)
    
    # ========================================================================
    # PERFORMANCE
    # ========================================================================
    avg_response_time_ms = models.IntegerField('Temps moyen de réponse (ms)', null=True, blank=True)
    timeout_seconds = models.IntegerField('Timeout (secondes)', default=30,
        validators=[MinValueValidator(5), MaxValueValidator(3600)])
    max_retries = models.IntegerField('Nombre max de tentatives', default=3,
        validators=[MinValueValidator(0), MaxValueValidator(10)])
    retry_delay_seconds = models.IntegerField('Délai entre tentatives', default=5)
    batch_size = models.IntegerField('Taille de lot', default=10000,
        validators=[MinValueValidator(1), MaxValueValidator(100000)])
    
    # ========================================================================
    # MÉTRIQUES DE PERFORMANCE
    # ========================================================================
    total_queries = models.BigIntegerField('Total requêtes', default=0)
    successful_queries = models.BigIntegerField('Requêtes réussies', default=0)
    failed_queries = models.BigIntegerField('Requêtes échouées', default=0)
    avg_query_time_ms = models.FloatField('Temps moyen requête (ms)', default=0)
    last_query_time = models.DateTimeField('Dernière requête', null=True, blank=True)
    
    # ========================================================================
    # GESTION DES ERREURS
    # ========================================================================
    error_count = models.IntegerField('Nombre d\'erreurs', default=0)
    last_error = models.TextField('Dernière erreur', blank=True)
    last_error_date = models.DateTimeField('Date dernière erreur', null=True, blank=True)
    consecutive_failures = models.IntegerField('Échecs consécutifs', default=0)
    
    # ========================================================================
    # ACCÈS ET ORGANISATION
    # ========================================================================
    is_public = models.BooleanField('Public', default=False)
    is_active = models.BooleanField('Actif', default=True, db_index=True)
    allowed_users = models.ManyToManyField(User, related_name='allowed_data_sources', blank=True)
    allowed_roles = models.JSONField('Rôles autorisés', default=list, blank=True)
    
    tags = models.JSONField('Tags', default=list, blank=True)
    category = models.CharField('Catégorie', max_length=100, blank=True, db_index=True)
    business_domain = models.CharField('Domaine métier', max_length=100, blank=True)
    owner_team = models.CharField('Équipe propriétaire', max_length=100, blank=True)
    
    # ========================================================================
    # MÉTADONNÉES
    # ========================================================================
    schema_info = models.JSONField('Informations schéma', default=dict, blank=True)
    sample_data = models.JSONField('Données échantillon', default=list, blank=True)
    metadata = models.JSONField('Métadonnées', default=dict, blank=True)
    documentation_url = models.URLField('URL documentation', blank=True)
    support_contact = models.EmailField('Contact support', blank=True)
    
    icon = models.CharField('Icône', max_length=50, blank=True)
    color = models.CharField('Couleur', max_length=20, blank=True)
    
    # ========================================================================
    # PROPRIÉTAIRES
    # ========================================================================
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='owned_data_sources', verbose_name='Propriétaire')
    team = models.ForeignKey('users.Team', on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='data_sources', verbose_name='Équipe')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_data_sources', verbose_name='Créé par')
    
    notes = models.TextField('Notes', blank=True)
    
    # Gestionnaire personnalisé
    objects = DataSourceManager()
    
    class Meta:
        db_table = 'data_sources'
        ordering = ['name']
        verbose_name = 'Source de données'
        verbose_name_plural = 'Sources de données'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['source_type', 'status']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['owner', 'team']),
            models.Index(fields=['-last_sync']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    # ========================================================================
    # PROPRIÉTÉS UTILES
    # ========================================================================
    @property
    def is_connected(self):
        """Vérifie si la source est connectée"""
        return self.status == 'active'
    
    @property
    def is_file_based(self):
        return self.source_type in ['excel', 'csv', 'json', 'xml', 'parquet', 'avro']
    
    @property
    def is_database(self):
        return self.source_type in ['postgresql', 'mysql', 'sqlserver', 'oracle', 'sqlite', 'db2']
    
    @property
    def is_nosql(self):
        return self.source_type in ['mongodb', 'elasticsearch', 'cassandra', 'redis', 'dynamodb']
    
    @property
    def is_cloud_dwh(self):
        return self.source_type in ['bigquery', 'snowflake', 'redshift', 'azure_sql', 'databricks']
    
    @property
    def is_api(self):
        return self.source_type in ['rest_api', 'graphql', 'soap', 'odata']
    
    @property
    def is_cloud_storage(self):
        return self.source_type in ['s3', 'azure_blob', 'gcs', 'google_drive', 'sharepoint', 'onedrive']
    
    @property
    def is_streaming(self):
        return self.source_type in ['kafka', 'kinesis']
    
    @property
    def success_rate(self):
        """Taux de succès des requêtes"""
        if self.total_queries == 0:
            return 100.0
        return (self.successful_queries / self.total_queries) * 100
    
    @property
    def data_size_mb(self):
        return round(self.data_size_bytes / (1024 * 1024), 2)
    
    @property
    def needs_sync(self):
        """Vérifie si une synchronisation est nécessaire"""
        if self.sync_frequency == 'manual' or not self.auto_refresh_enabled:
            return False
        if not self.next_sync:
            return True
        return timezone.now() >= self.next_sync
    
    @property
    def health_status(self):
        """État de santé de la source"""
        if self.consecutive_failures >= 5 or self.status == 'error':
            return 'critical'
        elif self.consecutive_failures >= 3 or self.error_count > 10:
            return 'warning'
        elif self.data_quality_score < 50:
            return 'poor'
        elif self.data_quality_score < 75:
            return 'fair'
        return 'good'
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    def test_connection(self):
        """Teste la connexion à la source de données"""
        from .services import DataSourceService
        service = DataSourceService(self)
        return service.test_connection()
    
    def execute_query(self, query, params=None):
        """Exécute une requête sur la source"""
        from .services import DataSourceService
        service = DataSourceService(self)
        return service.execute_query(query, params)
    
    def sync_tables(self):
        """Synchronise les tables de la source"""
        from .services import DataSourceService
        service = DataSourceService(self)
        return service.sync_tables()
    
    def log_error(self, error_message):
        """Enregistre une erreur"""
        self.error_count += 1
        self.consecutive_failures += 1
        self.last_error = error_message[:2000]
        self.last_error_date = timezone.now()
        if self.consecutive_failures >= 5:
            self.status = 'error'
        self.save(update_fields=['error_count', 'consecutive_failures', 'last_error', 'last_error_date', 'status'])
    
    def log_success(self, duration_ms=None):
        """Enregistre un succès"""
        self.consecutive_failures = 0
        self.last_error = ''
        self.last_sync = timezone.now()
        if duration_ms:
            self.last_sync_duration_ms = duration_ms
        if self.auto_refresh_enabled:
            self._calculate_next_sync()
        self.save(update_fields=['consecutive_failures', 'last_error', 'last_sync', 'last_sync_duration_ms', 'next_sync'])
    
    def _calculate_next_sync(self):
        """Calcule la prochaine synchronisation"""
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
        delta = freq_map.get(self.sync_frequency)
        if delta:
            self.next_sync = timezone.now() + delta
    
    def calculate_quality_score(self):
        """Calcule le score de qualité des données"""
        score = 100
        
        # Pénalités pour échecs consécutifs
        score -= min(self.consecutive_failures * 10, 30)
        
        # Pénalités pour données anciennes
        if self.last_sync:
            days_old = (timezone.now() - self.last_sync).days
            if days_old > 30:
                score -= 20
            elif days_old > 7:
                score -= 10
        
        # Pénalités pour non validation
        if not self.is_validated:
            score -= 15
        
        # Pénalités pour erreurs
        if self.error_count > 5:
            score -= min(self.error_count, 20)
        
        self.data_quality_score = max(score, 0)
        self.save(update_fields=['data_quality_score'])
        return self.data_quality_score


# ============================================================================
# TABLES DE DONNÉES
# ============================================================================

class DataTable(BaseModel):
    """
    Table d'une source de données
    """
    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE,
        related_name='tables', verbose_name='Source de données'
    )
    name = models.CharField('Nom de la table', max_length=200, validators=[validate_table_name])
    schema = models.CharField('Schéma', max_length=200, blank=True)
    catalog = models.CharField('Catalogue', max_length=200, blank=True)
    
    # Métadonnées
    description = models.TextField('Description', blank=True)
    row_count = models.BigIntegerField('Nombre de lignes', default=0, null=True, blank=True)
    size_bytes = models.BigIntegerField('Taille (octets)', default=0, null=True, blank=True)
    last_analyzed = models.DateTimeField('Dernière analyse', null=True, blank=True)
    
    # Schéma JSON (colonnes)
    columns = models.JSONField('Colonnes', default=list, blank=True)
    primary_key = models.JSONField('Clé primaire', default=list, blank=True)
    indexes = models.JSONField('Index', default=list, blank=True)
    foreign_keys = models.JSONField('Clés étrangères', default=list, blank=True)
    
    # Partitionnement
    is_partitioned = models.BooleanField('Partitionné', default=False)
    partition_column = models.CharField('Colonne de partition', max_length=200, blank=True)
    partition_count = models.IntegerField('Nombre de partitions', null=True, blank=True)
    
    # Statistiques
    last_updated = models.DateTimeField('Dernière mise à jour', null=True, blank=True)
    update_count = models.IntegerField('Nombre de mises à jour', default=0)
    
    objects = DataTableManager()
    
    class Meta:
        db_table = 'data_tables'
        ordering = ['data_source', 'schema', 'name']
        unique_together = ['data_source', 'schema', 'name']
        verbose_name = 'Table'
        verbose_name_plural = 'Tables'
        indexes = [
            models.Index(fields=['data_source', 'name']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name
    
    @property
    def full_name(self):
        """Nom complet avec schéma"""
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name
    
    @property
    def column_count(self):
        """Nombre de colonnes"""
        return len(self.columns) if self.columns else 0


# ============================================================================
# FICHIERS UPLOADÉS
# ============================================================================

class DataSourceFile(BaseModel):
    """
    Fichiers uploadés pour une source de données
    """
    # Utiliser FILE_PROCESS_STATUS importé
    PROCESS_STATUS = FILE_PROCESS_STATUS
    
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(
        'Fichier', upload_to='data_sources/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls', 'csv', 'json', 'xml', 'parquet', 'avro', 'txt'])]
    )
    original_name = models.CharField('Nom original', max_length=255)
    file_hash = models.CharField('Hash MD5', max_length=32, blank=True)
    file_size = models.BigIntegerField('Taille (octets)', default=0)
    mime_type = models.CharField('Type MIME', max_length=100, blank=True)
    
    # Structure
    row_count = models.BigIntegerField('Lignes', default=0)
    column_count = models.IntegerField('Colonnes', default=0)
    encoding = models.CharField('Encodage', max_length=50, default='utf-8', blank=True)
    delimiter = models.CharField('Délimiteur', max_length=5, blank=True)
    has_header = models.BooleanField('A en-tête', default=True)
    sheet_name = models.CharField('Nom de la feuille (Excel)', max_length=100, blank=True)
    
    # Traitement
    process_status = models.CharField('Statut traitement', max_length=20, choices=PROCESS_STATUS, default='pending', db_index=True)
    processed_at = models.DateTimeField('Traité le', null=True, blank=True)
    processing_errors = models.JSONField('Erreurs traitement', default=list, blank=True)
    processing_duration_ms = models.IntegerField('Durée traitement (ms)', null=True, blank=True)
    
    # Analyse
    preview_data = models.JSONField('Aperçu (10 premières lignes)', default=list, blank=True)
    schema = models.JSONField('Schéma détecté', default=dict, blank=True)
    column_types = models.JSONField('Types de colonnes', default=dict, blank=True)
    statistics = models.JSONField('Statistiques colonnes', default=dict, blank=True)
    null_counts = models.JSONField('Compteurs NULL', default=dict, blank=True)
    unique_counts = models.JSONField('Valeurs uniques', default=dict, blank=True)
    quality_issues = models.JSONField('Problèmes qualité', default=list, blank=True)
    
    # Versionnage
    version = models.IntegerField('Version', default=1)
    is_latest = models.BooleanField('Dernière version', default=True, db_index=True)
    replaces = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replaced_by')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    notes = models.TextField('Notes', blank=True)
    
    class Meta:
        db_table = 'data_source_files'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['data_source', '-created_at']),
            models.Index(fields=['process_status']),
            models.Index(fields=['is_latest']),
        ]
    
    def __str__(self):
        return f"{self.original_name} ({self.data_source.name})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_hash:
            hasher = hashlib.md5()
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.file_hash = hasher.hexdigest()
        if self.file:
            self.file_size = self.file.size
        if not self.original_name and self.file:
            self.original_name = self.file.name
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_processed(self):
        return self.process_status == 'completed'


# ============================================================================
# CONNEXION BASE DE DONNÉES
# ============================================================================

class DataSourceConnection(BaseModel):
    """
    Configuration de connexion base de données
    """
    data_source = models.OneToOneField(DataSource, on_delete=models.CASCADE, related_name='connection')
    
    # Paramètres de connexion
    host = models.CharField('Hôte', max_length=255)
    port = models.IntegerField('Port', validators=[MinValueValidator(1), MaxValueValidator(65535)])
    database_name = models.CharField('Base de données', max_length=255)
    schema_name = models.CharField('Schéma', max_length=255, blank=True)
    username = models.CharField('Nom d\'utilisateur', max_length=255, blank=True)
    password = models.CharField('Mot de passe', max_length=500, blank=True)
    extra_params = models.JSONField('Paramètres supplémentaires', default=dict, blank=True)
    
    # SSL
    use_ssl = models.BooleanField('SSL', default=True)
    ssl_mode = models.CharField('Mode SSL', max_length=50, default='require', blank=True)
    ssl_cert = models.TextField('Certificat SSL', blank=True)
    ssl_key = models.TextField('Clé SSL', blank=True)
    ssl_ca = models.TextField('Autorité SSL', blank=True)
    
    # Pool de connexions
    pool_size = models.IntegerField('Taille du pool', default=5, validators=[MinValueValidator(1), MaxValueValidator(50)])
    max_overflow = models.IntegerField('Dépassement max', default=10)
    pool_timeout = models.IntegerField('Timeout pool', default=30)
    connect_timeout = models.IntegerField('Timeout connexion', default=10)
    query_timeout = models.IntegerField('Timeout requête', default=30)
    
    # Statut
    is_connected = models.BooleanField('Connecté', default=False)
    last_connected = models.DateTimeField('Dernière connexion', null=True, blank=True)
    connection_test_result = models.JSONField('Résultat du test', default=dict, blank=True)
    latency_ms = models.IntegerField('Latence (ms)', null=True, blank=True)
    
    class Meta:
        db_table = 'data_source_connections'
    
    def __str__(self):
        return f"{self.host}:{self.port}/{self.database_name}"


# ============================================================================
# POWER QUERY - TRANSFORMATIONS M
# ============================================================================

class PowerQuery(BaseModel):
    """
    Power Query - Transformations en langage M
    """
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='power_queries', verbose_name='Source de données')
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    
    # Définition de la requête
    query_steps = models.JSONField('Étapes de transformation', default=list)
    m_code = models.TextField('Code M', blank=True)
    sql_query = models.TextField('Requête SQL', blank=True)
    output_schema = models.JSONField('Schéma de sortie', default=dict, blank=True)
    
    # Cache
    is_enabled = models.BooleanField('Activé', default=True)
    is_cached = models.BooleanField('Mettre en cache', default=False)
    cache_ttl_minutes = models.IntegerField('TTL cache (minutes)', default=60)
    
    # Exécution
    last_executed = models.DateTimeField('Dernière exécution', null=True, blank=True)
    execution_time_ms = models.IntegerField('Temps d\'exécution (ms)', null=True, blank=True)
    preview_result = models.JSONField('Résultat aperçu', default=dict, blank=True)
    result_row_count = models.BigIntegerField('Nombre de lignes résultat', default=0)
    execution_count = models.IntegerField('Nombre d\'exécutions', default=0)
    error_count = models.IntegerField('Nombre d\'erreurs', default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tags = models.JSONField('Tags', default=list, blank=True)
    
    class Meta:
        db_table = 'power_queries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.data_source.name})"


class QueryStep(BaseModel):
    """
    Étape individuelle dans un Power Query
    """
    # Utiliser QUERY_STEP_TYPES importé
    STEP_TYPES = QUERY_STEP_TYPES
    
    power_query = models.ForeignKey(PowerQuery, on_delete=models.CASCADE, related_name='steps')
    step_order = models.IntegerField('Ordre')
    step_type = models.CharField('Type', max_length=50, choices=STEP_TYPES)
    step_name = models.CharField('Nom de l\'étape', max_length=200, blank=True)
    step_config = models.JSONField('Configuration', default=dict)
    step_code = models.TextField('Code M', blank=True)
    is_enabled = models.BooleanField('Activé', default=True)
    description = models.TextField('Description', blank=True)
    preview_data = models.JSONField('Aperçu', default=list, blank=True)
    execution_time_ms = models.IntegerField('Temps d\'exécution (ms)', null=True, blank=True)
    error_message = models.TextField('Erreur', blank=True)
    
    class Meta:
        db_table = 'query_steps'
        ordering = ['step_order']
        unique_together = ['power_query', 'step_order']
    
    def __str__(self):
        return f"Étape {self.step_order}: {self.get_step_type_display()} ({self.power_query.name})"


# ============================================================================
# JOURNAUX ET HISTORIQUE
# ============================================================================

class DataSourceLog(BaseModel):
    """
    Journal des activités sur les sources de données
    """
    # Utiliser LOG_LEVEL_CHOICES importé
    LEVEL_CHOICES = LOG_LEVEL_CHOICES
    
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField('Niveau', max_length=20, choices=LEVEL_CHOICES, default='info')
    message = models.TextField('Message')
    
    # Détails
    query_id = models.CharField('ID requête', max_length=100, blank=True)
    query_text = models.TextField('Texte de la requête', blank=True)
    execution_time_ms = models.FloatField('Temps d\'exécution (ms)', null=True, blank=True)
    rows_affected = models.IntegerField('Lignes affectées', null=True, blank=True)
    
    # Données additionnelles
    data = models.JSONField('Données', default=dict, blank=True)
    stack_trace = models.TextField('Stack trace', blank=True)
    
    objects = DataSourceLogManager()
    
    class Meta:
        db_table = 'data_source_logs'
        ordering = ['-created_at']
        verbose_name = 'Journal source de données'
        verbose_name_plural = 'Journaux sources de données'
        indexes = [
            models.Index(fields=['data_source', '-created_at']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.data_source.name} - {self.level} - {self.created_at}"


class DataSourceMetric(BaseModel):
    """
    Métriques de performance des sources de données
    """
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField('Horodatage', auto_now_add=True, db_index=True)
    
    # Métriques de performance
    query_time_ms = models.FloatField('Temps de requête (ms)', null=True, blank=True)
    rows_returned = models.IntegerField('Lignes retournées', null=True, blank=True)
    cpu_time_ms = models.FloatField('Temps CPU (ms)', null=True, blank=True)
    io_wait_ms = models.FloatField('Attente I/O (ms)', null=True, blank=True)
    
    # Métriques réseau
    bytes_sent = models.BigIntegerField('Octets envoyés', null=True, blank=True)
    bytes_received = models.BigIntegerField('Octets reçus', null=True, blank=True)
    network_latency_ms = models.FloatField('Latence réseau (ms)', null=True, blank=True)
    
    # Métriques de connexion
    connection_time_ms = models.FloatField('Temps de connexion (ms)', null=True, blank=True)
    connection_pool_size = models.IntegerField('Taille du pool', null=True, blank=True)
    active_connections = models.IntegerField('Connexions actives', null=True, blank=True)
    
    # Métriques personnalisées
    custom_metrics = models.JSONField('Métriques personnalisées', default=dict, blank=True)
    
    objects = DataSourceMetricManager()
    
    class Meta:
        db_table = 'data_source_metrics'
        ordering = ['-timestamp']
        verbose_name = 'Métrique source de données'
        verbose_name_plural = 'Métriques sources de données'
        indexes = [
            models.Index(fields=['data_source', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.data_source.name} - {self.timestamp}"


class DataSourceHistory(BaseModel):
    """
    Historique des changements sur les sources de données
    """
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='history')
    field = models.CharField('Champ modifié', max_length=100)
    old_value = models.TextField('Ancienne valeur', blank=True)
    new_value = models.TextField('Nouvelle valeur', blank=True)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='data_source_changes', verbose_name='Modifié par'
    )
    reason = models.CharField('Raison', max_length=500, blank=True)
    
    class Meta:
        db_table = 'data_source_history'
        ordering = ['-created_at']
        verbose_name = 'Historique source de données'
        verbose_name_plural = 'Historiques sources de données'
        indexes = [
            models.Index(fields=['data_source', '-created_at']),
            models.Index(fields=['field']),
        ]
    
    def __str__(self):
        return f"{self.data_source.name} - {self.field} - {self.created_at}"

# apps/data_sources/models.py - AJOUTER APRÈS DataTable

# ============================================================================
# REQUÊTES ENREGISTRÉES
# ============================================================================

class DataQuery(BaseModel):
    """
    Requête enregistrée pour une source de données
    """
    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE,
        related_name='saved_queries', verbose_name='Source de données'
    )
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    query_type = models.CharField(
        'Type de requête',
        max_length=20,
        choices=QUERY_TYPES,
        default='sql'
    )
    
    # Requête
    query_text = models.TextField('Texte de la requête', validators=[validate_sql_query])
    parameters = models.JSONField('Paramètres', default=list, blank=True)
    
    # Métadonnées
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_queries', verbose_name='Créé par'
    )
    is_favorite = models.BooleanField('Favori', default=False)
    is_public = models.BooleanField('Public', default=False)
    tags = models.JSONField('Tags', default=list, blank=True)
    
    # Statistiques
    execution_count = models.IntegerField('Nombre d\'exécutions', default=0)
    avg_execution_time_ms = models.FloatField('Temps moyen (ms)', default=0)
    last_executed = models.DateTimeField('Dernière exécution', null=True, blank=True)
    
    # Cache
    cached_result = models.JSONField('Résultat en cache', default=dict, blank=True)
    cached_at = models.DateTimeField('Mis en cache le', null=True, blank=True)
    cache_ttl = models.IntegerField('TTL cache (secondes)', default=300)
    is_cached = models.BooleanField('En cache', default=False)
    
    objects = DataQueryManager()
    
    class Meta:
        db_table = 'data_queries'
        ordering = ['-is_favorite', 'name']
        verbose_name = 'Requête'
        verbose_name_plural = 'Requêtes'
        indexes = [
            models.Index(fields=['data_source', 'name']),
            models.Index(fields=['is_favorite']),
            models.Index(fields=['created_by']),
            models.Index(fields=['-last_executed']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.data_source.name})"
    
    def execute(self, params=None):
        """Exécute la requête"""
        from .services import QueryService
        service = QueryService(self)
        return service.execute(params)
    
    def clear_cache(self):
        """Vide le cache de la requête"""
        self.cached_result = {}
        self.cached_at = None
        self.save(update_fields=['cached_result', 'cached_at'])

# apps/data_sources/models.py - AJOUTER APRÈS DataQuery

# ============================================================================
# SCHÉMAS EN ÉTOILE (STAR SCHEMA)
# ============================================================================

class StarSchema(BaseModel):
    """
    Schéma en étoile (Star Schema) pour le data warehouse
    Permet de modéliser des données pour l'analyse BI
    """
    name = models.CharField('Nom', max_length=200, db_index=True)
    description = models.TextField('Description', blank=True)
    
    # Table des faits
    fact_table = models.ForeignKey(
        DataTable,
        on_delete=models.CASCADE,
        related_name='star_schemas_fact',
        verbose_name='Table des faits',
        help_text="Table contenant les mesures (faits)"
    )
    
    # Tables de dimensions
    dimension_tables = models.ManyToManyField(
        DataTable,
        related_name='star_schemas_dimension',
        verbose_name='Tables de dimensions',
        help_text="Tables contenant les attributs descriptifs"
    )
    
    # Configuration des colonnes
    fact_columns = models.JSONField(
        'Colonnes des faits',
        default=list,
        blank=True,
        help_text="Liste des colonnes à utiliser comme mesures"
    )
    
    dimension_columns = models.JSONField(
        'Colonnes des dimensions',
        default=dict,
        blank=True,
        help_text="Dictionnaire {nom_dimension: [colonnes]} ou {nom_dimension: colonne_unique}"
    )
    
    measures = models.JSONField(
        'Mesures',
        default=list,
        blank=True,
        help_text="Liste des mesures avec agrégations: [{'column': 'montant', 'aggregation': 'SUM', 'alias': 'total'}]"
    )
    
    # Relations entre tables
    relationships = models.JSONField(
        'Relations',
        default=dict,
        blank=True,
        help_text="Dictionnaire des relations entre faits et dimensions"
    )
    
    # Configuration du grain
    grain = models.CharField(
        'Grain',
        max_length=200,
        blank=True,
        help_text="Niveau de détail (ex: 'par jour', 'par produit')"
    )
    
    # Propriétaire
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='star_schemas',
        verbose_name='Propriétaire'
    )
    
    # Équipe
    team = models.ForeignKey(
        'users.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='star_schemas',
        verbose_name='Équipe'
    )
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    is_active = models.BooleanField('Actif', default=True, db_index=True)
    is_public = models.BooleanField('Public', default=False)
    
    # Statistiques
    query_count = models.IntegerField('Nombre de requêtes', default=0)
    last_queried_at = models.DateTimeField('Dernière requête', null=True, blank=True)
    
    class Meta:
        db_table = 'star_schemas'
        ordering = ['name']
        verbose_name = 'Schéma en étoile'
        verbose_name_plural = 'Schémas en étoile'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def dimension_tables_count(self):
        """Nombre de tables de dimensions"""
        return self.dimension_tables.count()
    
    @property
    def measures_count(self):
        """Nombre de mesures"""
        return len(self.measures) if self.measures else 0
    
    def generate_query(self) -> str:
        """
        Génère la requête SQL pour ce schéma en étoile
        """
        fact_table = self.fact_table.full_name
        
        # Construire les SELECT
        select_parts = []
        
        # Dimensions
        for dim_name, dim_config in self.dimension_columns.items():
            if isinstance(dim_config, list):
                for col in dim_config:
                    select_parts.append(f"{dim_name}.{col} AS {dim_name}_{col}")
            elif isinstance(dim_config, str):
                select_parts.append(f"{dim_name}.{dim_config} AS {dim_name}")
            elif isinstance(dim_config, dict):
                for alias, col in dim_config.items():
                    select_parts.append(f"{dim_name}.{col} AS {alias}")
        
        # Mesures
        for measure in self.measures:
            agg_func = measure.get('aggregation', 'SUM').upper()
            column = measure.get('column')
            alias = measure.get('alias', column)
            select_parts.append(f"{agg_func}({fact_table}.{column}) AS {alias}")
        
        # Construire les JOIN
        join_parts = []
        for dim_name, dim_table in self.dimension_columns.items():
            # Chercher la table de dimension
            dim_table_obj = self.dimension_tables.filter(name=dim_table).first()
            if not dim_table_obj:
                dim_table_obj = self.dimension_tables.filter(full_name=dim_name).first()
            
            if dim_table_obj:
                join_parts.append(
                    f"LEFT JOIN {dim_table_obj.full_name} AS {dim_name} "
                    f"ON {fact_table}.{dim_name}_id = {dim_name}.id"
                )
        
        # Construire le GROUP BY
        group_by_parts = []
        for dim_name, dim_config in self.dimension_columns.items():
            if isinstance(dim_config, list):
                for col in dim_config:
                    group_by_parts.append(f"{dim_name}.{col}")
            elif isinstance(dim_config, str):
                group_by_parts.append(f"{dim_name}.{dim_config}")
            elif isinstance(dim_config, dict):
                for col in dim_config.values():
                    group_by_parts.append(f"{dim_name}.{col}")
        
        # Construire la requête complète
        query = f"""
        SELECT {', '.join(select_parts)}
        FROM {fact_table}
        {' '.join(join_parts)}
        GROUP BY {', '.join(group_by_parts)}
        """
        
        return query.strip()
    
    def get_sql(self) -> str:
        """Alias pour generate_query"""
        return self.generate_query()