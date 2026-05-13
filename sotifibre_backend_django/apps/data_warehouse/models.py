# apps/data_warehouse/models.py
"""
Modèles avancés pour l'application data_warehouse - Data Warehouse BI
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

from apps.core.models import BaseModel, SoftDeleteModel
from apps.users.models import User
from apps.data_sources.models import DataSource, DataTable

from .constants import (
    TABLE_TYPES, DIMENSION_TYPES, SCD_TYPES, GRANULARITIES,
    AGGREGATION_TYPES, PARTITION_TYPES, TABLE_STATUS, REFRESH_FREQUENCIES, COLUMN_TYPES
)
from .validators import (
    validate_sql_query, validate_table_name, validate_column_name,
    validate_partition_expression
)
from .managers import (
    FactTableManager, DimensionTableManager, AggregateTableManager,
    TableManager, ColumnManager, IndexManager
)


# ============================================================================
# SCHEMAS DATA WAREHOUSE
# ============================================================================

class DataWarehouseSchema(BaseModel):
    """
    Schéma du Data Warehouse (namespace pour organiser les tables)
    """
    name = models.CharField('Nom du schéma', max_length=100, unique=True, db_index=True)
    description = models.TextField('Description', blank=True)
    
    # Configuration
    default_tablespace = models.CharField('Tablespace par défaut', max_length=100, blank=True)
    default_compression = models.BooleanField('Compression par défaut', default=True)
    
    # Métadonnées
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='owned_dw_schemas', verbose_name='Propriétaire'
    )
    tags = models.JSONField('Tags', default=list, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    
    # Statistiques
    table_count = models.IntegerField('Nombre de tables', default=0)
    size_bytes = models.BigIntegerField('Taille totale (octets)', default=0)
    last_analyzed = models.DateTimeField('Dernière analyse', null=True, blank=True)
    
    class Meta:
        db_table = 'data_warehouse_schemas'
        ordering = ['name']
        verbose_name = 'Schéma Data Warehouse'
        verbose_name_plural = 'Schémas Data Warehouse'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def size_mb(self):
        return round(self.size_bytes / (1024 * 1024), 2)


# ============================================================================
# TABLES DATA WAREHOUSE
# ============================================================================

class DataWarehouseTable(BaseModel):
    """
    Table de Data Warehouse (Fact, Dimension, Aggregate, Bridge, Staging)
    """
    # Identité
    name = models.CharField('Nom de la table', max_length=200, db_index=True)
    schema = models.ForeignKey(
        DataWarehouseSchema, on_delete=models.CASCADE,
        related_name='tables', verbose_name='Schéma'
    )
    table_type = models.CharField(
        'Type de table', max_length=20, choices=TABLE_TYPES, db_index=True
    )
    description = models.TextField('Description', blank=True)
    status = models.CharField('Statut', max_length=20, choices=TABLE_STATUS, default='active')
    
    # Source de données (optionnelle - si la table est alimentée par ETL)
    source_table = models.ForeignKey(
        DataTable, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dw_tables', verbose_name='Table source'
    )
    source_pipeline = models.ForeignKey(
        'etl_engine.ETLPipeline', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dw_tables', verbose_name='Pipeline ETL source'
    )
    
    # Configuration dimensionnelle
    dimension_type = models.CharField(
        'Type de dimension', max_length=20, choices=DIMENSION_TYPES,
        blank=True, null=True, help_text="Pour les tables de dimension"
    )
    scd_type = models.CharField(
        'Type SCD', max_length=10, choices=SCD_TYPES, blank=True, null=True,
        help_text="Pour les dimensions à évolution lente"
    )
    granularity = models.CharField(
        'Granularité', max_length=20, choices=GRANULARITIES, blank=True, null=True,
        help_text="Pour les tables de faits"
    )
    
    # Colonnes
    columns = models.JSONField('Colonnes', default=list, blank=True)
    primary_key = models.JSONField('Clé primaire', default=list, blank=True)
    foreign_keys = models.JSONField('Clés étrangères', default=list, blank=True)
    indexes = models.JSONField('Index', default=list, blank=True)
    
    # Partitionnement
    is_partitioned = models.BooleanField('Partitionné', default=False)
    partition_column = models.CharField('Colonne de partition', max_length=200, blank=True)
    partition_type = models.CharField(
        'Type de partition', max_length=20, choices=PARTITION_TYPES, blank=True
    )
    partition_expression = models.TextField(
        'Expression de partition', blank=True, validators=[validate_partition_expression]
    )
    partition_count = models.IntegerField('Nombre de partitions', null=True, blank=True)
    
    # Compression et stockage
    is_compressed = models.BooleanField('Compressé', default=False)
    tablespace = models.CharField('Tablespace', max_length=100, blank=True)
    row_count = models.BigIntegerField('Nombre de lignes', default=0)
    size_bytes = models.BigIntegerField('Taille (octets)', default=0)
    
    # Rafraîchissement
    refresh_frequency = models.CharField(
        'Fréquence de rafraîchissement', max_length=20, choices=REFRESH_FREQUENCIES,
        default='daily'
    )
    last_refresh = models.DateTimeField('Dernier rafraîchissement', null=True, blank=True)
    next_refresh = models.DateTimeField('Prochain rafraîchissement', null=True, blank=True)
    refresh_duration_ms = models.IntegerField('Durée rafraîchissement (ms)', null=True, blank=True)
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    business_owner = models.CharField('Propriétaire métier', max_length=200, blank=True)
    technical_owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='owned_dw_tables', verbose_name='Propriétaire technique'
    )
    documentation_url = models.URLField('URL documentation', blank=True)
    
    objects = TableManager()
    facts = FactTableManager()
    dimensions = DimensionTableManager()
    aggregates = AggregateTableManager()
    
    class Meta:
        db_table = 'data_warehouse_tables'
        ordering = ['schema', 'name']
        unique_together = ['schema', 'name']
        verbose_name = 'Table Data Warehouse'
        verbose_name_plural = 'Tables Data Warehouse'
        indexes = [
            models.Index(fields=['schema', 'name']),
            models.Index(fields=['table_type']),
            models.Index(fields=['status']),
            models.Index(fields=['-last_refresh']),
        ]
    
    def __str__(self):
        return f"{self.schema.name}.{self.name} ({self.get_table_type_display()})"
    
    @property
    def full_name(self):
        """Nom complet avec schéma"""
        return f"{self.schema.name}.{self.name}"
    
    @property
    def size_mb(self):
        return round(self.size_bytes / (1024 * 1024), 2)
    
    @property
    def needs_refresh(self):
        if self.refresh_frequency == 'manual' or self.status != 'active':
            return False
        if not self.next_refresh:
            return True
        return timezone.now() >= self.next_refresh
    
    def calculate_next_refresh(self):
        """Calcule la prochaine date de rafraîchissement"""
        freq_map = {
            'realtime': timedelta(seconds=10),
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
        }
        delta = freq_map.get(self.refresh_frequency)
        if delta:
            self.next_refresh = timezone.now() + delta
            self.save(update_fields=['next_refresh'])
    
    def update_stats(self):
        """Met à jour les statistiques de la table"""
        # À implémenter avec des requêtes SQL
        pass


# ============================================================================
# FAITS ET MESURES
# ============================================================================

class FactTable(DataWarehouseTable):
    """
    Table des faits (proxy pour les tables de type fact)
    """
    class Meta:
        proxy = True
        verbose_name = 'Table des faits'
        verbose_name_plural = 'Tables des faits'
    
    def save(self, *args, **kwargs):
        self.table_type = 'fact'
        super().save(*args, **kwargs)
    
    def add_measure(self, name, column, aggregation_type, **kwargs):
        """Ajoute une mesure à la table des faits"""
        measure = Measure.objects.create(
            fact_table=self,
            name=name,
            column=column,
            aggregation_type=aggregation_type,
            **kwargs
        )
        return measure


class DimensionTable(DataWarehouseTable):
    """
    Table de dimension (proxy pour les tables de type dimension)
    """
    class Meta:
        proxy = True
        verbose_name = 'Table de dimension'
        verbose_name_plural = 'Tables de dimension'
    
    def save(self, *args, **kwargs):
        self.table_type = 'dimension'
        super().save(*args, **kwargs)
    
    def add_attribute(self, name, column, data_type, **kwargs):
        """Ajoute un attribut à la dimension"""
        attribute = DimensionAttribute.objects.create(
            dimension_table=self,
            name=name,
            column=column,
            data_type=data_type,
            **kwargs
        )
        return attribute


class Measure(BaseModel):
    """
    Mesure dans une table des faits
    """
    fact_table = models.ForeignKey(
        FactTable, on_delete=models.CASCADE, related_name='measures',
        verbose_name='Table des faits'
    )
    name = models.CharField('Nom de la mesure', max_length=200)
    column = models.CharField('Colonne source', max_length=200)
    aggregation_type = models.CharField(
        'Type d\'agrégation', max_length=20, choices=AGGREGATION_TYPES
    )
    alias = models.CharField('Alias', max_length=200, blank=True)
    description = models.TextField('Description', blank=True)
    
    # Configuration
    is_calculated = models.BooleanField('Mesure calculée', default=False)
    formula = models.TextField('Formule', blank=True, help_text="Pour les mesures calculées")
    
    # Formatage
    format_string = models.CharField('Format', max_length=50, blank=True)
    unit = models.CharField('Unité', max_length=50, blank=True)
    decimal_places = models.IntegerField('Décimales', default=2)
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    
    class Meta:
        db_table = 'data_warehouse_measures'
        ordering = ['fact_table', 'name']
        verbose_name = 'Mesure'
        verbose_name_plural = 'Mesures'
        indexes = [
            models.Index(fields=['fact_table', 'name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.fact_table.name}.{self.name}"
    
    @property
    def full_name(self):
        if self.alias:
            return self.alias
        return self.name


class DimensionAttribute(BaseModel):
    """
    Attribut dans une table de dimension
    """
    dimension_table = models.ForeignKey(
        DimensionTable, on_delete=models.CASCADE, related_name='attributes',
        verbose_name='Table de dimension'
    )
    name = models.CharField('Nom de l\'attribut', max_length=200)
    column = models.CharField('Colonne source', max_length=200)
    data_type = models.CharField('Type de données', max_length=20, choices=COLUMN_TYPES)
    description = models.TextField('Description', blank=True)
    
    # Configuration
    is_key = models.BooleanField('Clé de dimension', default=False)
    is_hierarchical = models.BooleanField('Hiérarchique', default=False)
    parent_attribute = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', verbose_name='Attribut parent'
    )
    
    # Formatage
    format_string = models.CharField('Format', max_length=50, blank=True)
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    
    class Meta:
        db_table = 'data_warehouse_dimension_attributes'
        ordering = ['dimension_table', 'name']
        verbose_name = 'Attribut de dimension'
        verbose_name_plural = 'Attributs de dimension'
        indexes = [
            models.Index(fields=['dimension_table', 'name']),
            models.Index(fields=['is_key']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.dimension_table.name}.{self.name}"


# ============================================================================
# SCHÉMAS EN ÉTOILE
# ============================================================================

class StarSchema(BaseModel):
    """
    Schéma en étoile complet (liaison fait-dimensions)
    """
    name = models.CharField('Nom', max_length=200, db_index=True)
    description = models.TextField('Description', blank=True)
    
    # Tables
    fact_table = models.ForeignKey(
        FactTable, on_delete=models.CASCADE, related_name='star_schemas_fact',
        verbose_name='Table des faits'
    )
    dimension_tables = models.ManyToManyField(
        DimensionTable, related_name='star_schemas_dimension',
        verbose_name='Tables de dimensions'
    )
    
    # Configuration
    fact_columns = models.JSONField('Colonnes des faits', default=list, blank=True)
    dimension_columns = models.JSONField('Colonnes des dimensions', default=dict, blank=True)
    relationships = models.JSONField('Relations', default=dict, blank=True)
    
    # Métadonnées
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dw_star_schemas', verbose_name='Propriétaire'
    )
    tags = models.JSONField('Tags', default=list, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    
    # Statistiques
    query_count = models.IntegerField('Nombre de requêtes', default=0)
    last_queried_at = models.DateTimeField('Dernière requête', null=True, blank=True)
    avg_query_time_ms = models.FloatField('Temps moyen de requête (ms)', default=0)
    
    class Meta:
        db_table = 'data_warehouse_star_schemas'
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
    def dimension_count(self):
        return self.dimension_tables.count()
    
    @property
    def measure_count(self):
        return self.fact_table.measures.count()
    
    def generate_query(self) -> str:
        """Génère la requête SQL pour ce schéma en étoile"""
        fact_table = self.fact_table.full_name
        
        # Construire les SELECT
        select_parts = []
        
        # Dimensions
        for dim in self.dimension_tables.all():
            for attr in dim.attributes.filter(is_active=True):
                select_parts.append(f"{dim.full_name}.{attr.column} AS {dim.name}_{attr.name}")
        
        # Mesures
        for measure in self.fact_table.measures.filter(is_active=True):
            agg_func = measure.aggregation_type.upper()
            alias = measure.alias or measure.name
            select_parts.append(f"{agg_func}({fact_table}.{measure.column}) AS {alias}")
        
        # Construire les JOIN
        join_parts = []
        for dim in self.dimension_tables.all():
            join_parts.append(
                f"LEFT JOIN {dim.full_name} ON {fact_table}.{dim.name}_id = {dim.full_name}.id"
            )
        
        # Construire le GROUP BY
        group_by_parts = []
        for dim in self.dimension_tables.all():
            for attr in dim.attributes.filter(is_active=True):
                group_by_parts.append(f"{dim.full_name}.{attr.column}")
        
        query = f"""
        SELECT {', '.join(select_parts)}
        FROM {fact_table}
        {' '.join(join_parts)}
        GROUP BY {', '.join(group_by_parts)}
        """
        
        return query.strip()
    
    def execute(self, limit=None, params=None):
        """Exécute la requête sur la base data_warehouse"""
        from .services import StarSchemaService
        service = StarSchemaService(self)
        return service.execute(limit, params)


# ============================================================================
# AGRÉGATIONS
# ============================================================================

class AggregationTable(BaseModel):
    """
    Table d'agrégation pour optimiser les performances
    """
    name = models.CharField('Nom', max_length=200)
    base_table = models.ForeignKey(
        DataWarehouseTable, on_delete=models.CASCADE,
        related_name='aggregations', verbose_name='Table de base'
    )
    granularity = models.CharField(
        'Granularité', max_length=20, choices=GRANULARITIES
    )
    group_by_columns = models.JSONField('Colonnes de groupement', default=list)
    aggregated_columns = models.JSONField('Colonnes agrégées', default=dict)
    
    # Configuration
    refresh_frequency = models.CharField(
        'Fréquence de rafraîchissement', max_length=20, choices=REFRESH_FREQUENCIES,
        default='daily'
    )
    last_refresh = models.DateTimeField('Dernier rafraîchissement', null=True, blank=True)
    
    # Métadonnées
    row_count = models.BigIntegerField('Nombre de lignes', default=0)
    size_bytes = models.BigIntegerField('Taille (octets)', default=0)
    compression_ratio = models.FloatField('Taux de compression', default=1.0)
    
    objects = AggregateTableManager()
    
    class Meta:
        db_table = 'data_warehouse_aggregations'
        ordering = ['base_table', 'granularity']
        verbose_name = 'Table d\'agrégation'
        verbose_name_plural = 'Tables d\'agrégation'
        indexes = [
            models.Index(fields=['base_table', 'granularity']),
        ]
    
    def __str__(self):
        return f"{self.base_table.name}_agg_{self.granularity}"
    
    @property
    def size_mb(self):
        return round(self.size_bytes / (1024 * 1024), 2)


# ============================================================================
# JOURNAUX ET MÉTRIQUES
# ============================================================================

class DataWarehouseLog(BaseModel):
    """
    Journal des opérations Data Warehouse
    """
    LEVEL_CHOICES = [
        ('info', 'ℹ️ Info'),
        ('warning', '⚠️ Warning'),
        ('error', '❌ Error'),
        ('debug', '🐛 Debug'),
    ]
    
    OPERATION_CHOICES = [
        ('refresh', '🔄 Rafraîchissement'),
        ('query', '📊 Requête'),
        ('optimize', '⚡ Optimisation'),
        ('analyze', '🔍 Analyse'),
        ('partition', '📁 Partitionnement'),
    ]
    
    table = models.ForeignKey(
        DataWarehouseTable, on_delete=models.CASCADE,
        related_name='logs', null=True, blank=True,
        verbose_name='Table concernée'
    )
    operation = models.CharField('Opération', max_length=20, choices=OPERATION_CHOICES)
    level = models.CharField('Niveau', max_length=20, choices=LEVEL_CHOICES, default='info')
    message = models.TextField('Message')
    
    # Détails
    duration_ms = models.FloatField('Durée (ms)', null=True, blank=True)
    rows_affected = models.BigIntegerField('Lignes affectées', null=True, blank=True)
    query = models.TextField('Requête SQL', blank=True)
    metadata = models.JSONField('Métadonnées', default=dict, blank=True)
    stack_trace = models.TextField('Stack trace', blank=True)
    
    class Meta:
        db_table = 'data_warehouse_logs'
        ordering = ['-created_at']
        verbose_name = 'Journal Data Warehouse'
        verbose_name_plural = 'Journaux Data Warehouse'
        indexes = [
            models.Index(fields=['table', '-created_at']),
            models.Index(fields=['operation']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.get_operation_display()} - {self.message[:50]}"


class DataWarehouseMetric(BaseModel):
    """
    Métriques de performance Data Warehouse
    """
    table = models.ForeignKey(
        DataWarehouseTable, on_delete=models.CASCADE,
        related_name='metrics', verbose_name='Table concernée'
    )
    timestamp = models.DateTimeField('Horodatage', auto_now_add=True, db_index=True)
    
    # Métriques de performance
    query_time_ms = models.FloatField('Temps de requête (ms)', null=True, blank=True)
    rows_scanned = models.BigIntegerField('Lignes scannées', null=True, blank=True)
    bytes_read = models.BigIntegerField('Octets lus', null=True, blank=True)
    cache_hit_ratio = models.FloatField('Taux de cache', null=True, blank=True)
    
    # Métriques de stockage
    table_size_bytes = models.BigIntegerField('Taille table (octets)', null=True, blank=True)
    index_size_bytes = models.BigIntegerField('Taille index (octets)', null=True, blank=True)
    partition_count = models.IntegerField('Nombre de partitions', null=True, blank=True)
    
    # Métriques de compression
    compressed_size_bytes = models.BigIntegerField('Taille compressée', null=True, blank=True)
    compression_ratio = models.FloatField('Taux de compression', null=True, blank=True)
    
    # Métriques personnalisées
    custom_metrics = models.JSONField('Métriques personnalisées', default=dict, blank=True)
    
    class Meta:
        db_table = 'data_warehouse_metrics'
        ordering = ['-timestamp']
        verbose_name = 'Métrique Data Warehouse'
        verbose_name_plural = 'Métriques Data Warehouse'
        indexes = [
            models.Index(fields=['table', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.table.name} - {self.timestamp}"
