# apps/star_schema/models.py
"""
Star Schema Models - Modélisation dimensionnelle avancée
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel
from apps.users.models import User
from apps.data_warehouse.models import FactTable, DimensionTable, Measure
from apps.data_sources.models import StarSchema as DataSourceStarSchema  # Importer l'existant

from .constants import (
    SCHEMA_TYPES, RELATION_TYPES, JOIN_TYPES, GRAIN_LEVELS,
    STATUS_CHOICES, CALCULATION_TYPES
)
from .validators import (
    validate_schema_name, validate_relation_definition,
    validate_dimension_mapping, validate_measure_definition,
    validate_filter_expression, validate_calculation_formula,
    validate_schema_graph
)
from .managers import DimensionalSchemaManager, FactRelationshipManager


# ============================================================================
# SCHÉMA DIMENSIONNEL PRINCIPAL (renommé pour éviter conflit)
# ============================================================================

class DimensionalSchema(BaseModel):  # ← Renommé de StarSchema à DimensionalSchema
    """
    Schéma dimensionnel avancé pour la modélisation BI
    Supporte les schémas en étoile, flocon, galaxie et constellations
    """
    
    # Informations de base
    name = models.CharField(
        'Nom du schéma',
        max_length=200,
        db_index=True,
        validators=[validate_schema_name]
    )
    description = models.TextField('Description', blank=True)
    schema_type = models.CharField(
        'Type de schéma',
        max_length=20,
        choices=SCHEMA_TYPES,
        default='star'
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    version = models.CharField('Version', max_length=20, default='1.0')
    
    # Tables principales
    fact_tables = models.ManyToManyField(
        FactTable,
        related_name='dimensional_schemas_as_fact',  # ← related_name unique
        verbose_name='Tables de faits'
    )
    dimension_tables = models.ManyToManyField(
        DimensionTable,
        related_name='dimensional_schemas_as_dimension',  # ← related_name unique
        verbose_name='Tables de dimensions',
        blank=True
    )
    
    # Relations entre tables
    relationships = models.JSONField(
        'Relations',
        default=list,
        blank=True,
        validators=[validate_relation_definition],
        help_text="Définition des relations entre tables"
    )
    
    # Mapping des dimensions
    dimension_mapping = models.JSONField(
        'Mapping des dimensions',
        default=dict,
        blank=True,
        validators=[validate_dimension_mapping],
        help_text="Mapping des colonnes de dimensions"
    )
    
    # Mesures
    measures = models.ManyToManyField(
        Measure,
        related_name='dimensional_schemas_as_measure',  # ← related_name unique
        verbose_name='Mesures',
        blank=True
    )
    
    # Configuration des mesures (JSON pour flexibilité)
    measure_config = models.JSONField(
        'Configuration des mesures',
        default=list,
        blank=True,
        validators=[validate_measure_definition],
        help_text="Configuration avancée des mesures (alias, format, etc.)"
    )
    
    # Calculs personnalisés
    calculations = models.JSONField(
        'Calculs personnalisés',
        default=list,
        blank=True,
        help_text="Formules de calcul personnalisées"
    )
    
    # Filtres par défaut
    default_filters = models.JSONField(
        'Filtres par défaut',
        default=list,
        blank=True,
        validators=[validate_filter_expression],
        help_text="Filtres appliqués par défaut"
    )
    
    # Grain du schéma
    grain = models.CharField(
        'Grain',
        max_length=20,
        choices=GRAIN_LEVELS,
        default='transaction'
    )
    
    # Configuration des jointures
    default_join_type = models.CharField(
        'Type de jointure par défaut',
        max_length=20,
        choices=JOIN_TYPES,
        default='left'
    )
    
    # Métadonnées
    tags = models.JSONField('Tags', default=list, blank=True)
    category = models.CharField('Catégorie', max_length=100, blank=True)
    business_domain = models.CharField('Domaine métier', max_length=100, blank=True)
    documentation_url = models.URLField('URL documentation', blank=True)
    
    # Propriétaires
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_dimensional_schemas',  # ← related_name unique
        verbose_name='Propriétaire'
    )
    team = models.ForeignKey(
        'users.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dimensional_schemas',  # ← related_name unique pour éviter conflit
        verbose_name='Équipe'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_dimensional_schemas',  # ← related_name unique
        verbose_name='Créé par'
    )
    
    # Statistiques d'utilisation
    query_count = models.IntegerField('Nombre de requêtes', default=0)
    last_queried_at = models.DateTimeField('Dernière requête', null=True, blank=True)
    avg_query_time_ms = models.FloatField('Temps moyen de requête (ms)', default=0)
    
    # Performance
    is_cached = models.BooleanField('Mise en cache', default=False)
    cache_ttl_seconds = models.IntegerField('TTL cache (secondes)', default=300)
    
    # Gestionnaire personnalisé
    objects = DimensionalSchemaManager()
    
    class Meta:
        db_table = 'dimensional_schemas'  # ← Nouveau nom de table
        ordering = ['name']
        verbose_name = 'Schéma dimensionnel'
        verbose_name_plural = 'Schémas dimensionnels'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['schema_type', 'status']),
            models.Index(fields=['owner', 'team']),
            models.Index(fields=['-query_count']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_schema_type_display()})"
    
    @property
    def fact_table_count(self):
        """Nombre de tables de faits"""
        return self.fact_tables.count()
    
    @property
    def dimension_table_count(self):
        """Nombre de tables de dimensions"""
        return self.dimension_tables.count()
    
    @property
    def measure_count(self):
        """Nombre de mesures"""
        return self.measures.count()
    
    @property
    def is_active(self):
        """Vérifie si le schéma est actif"""
        return self.status == 'active'
    
    def generate_query(self, filters=None, limit=None, offset=None):
        """
        Génère la requête SQL pour ce schéma dimensionnel
        """
        if not self.fact_tables.exists():
            return ""
        
        fact_table = self.fact_tables.first()
        
        select_parts = []
        group_by_parts = []
        
        # Ajouter les dimensions
        for dim_name, dim_config in self.dimension_mapping.items():
            if isinstance(dim_config, dict):
                for alias, column in dim_config.items():
                    select_parts.append(f"{dim_name}.{column} AS {alias}")
                    group_by_parts.append(f"{dim_name}.{column}")
            elif isinstance(dim_config, list):
                for column in dim_config:
                    select_parts.append(f"{dim_name}.{column}")
                    group_by_parts.append(f"{dim_name}.{column}")
            else:
                select_parts.append(f"{dim_name}.{dim_config}")
                group_by_parts.append(f"{dim_name}.{dim_config}")
        
        # Ajouter les mesures
        for measure in self.measures.all():
            agg_func = measure.get_aggregation_type_display().upper()
            column = measure.column
            alias = measure.alias or measure.name
            select_parts.append(f"{agg_func}({fact_table.name}.{column}) AS {alias}")
        
        # Ajouter les calculs personnalisés
        for calc in self.calculations:
            formula = calc.get('formula', '')
            alias = calc.get('alias', 'calc')
            select_parts.append(f"({formula}) AS {alias}")
        
        if select_parts:
            query = f"""
            SELECT {', '.join(select_parts)}
            FROM {fact_table.name}
            {self._build_join_clause()}
            {self._build_where_clause(filters)}
            GROUP BY {', '.join(group_by_parts) if group_by_parts else '1'}
            """
            
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            return query.strip()
        
        return ""
    
    def _build_join_clause(self):
        """Construit la clause JOIN"""
        joins = []
        for relation in self.relationships:
            join_type = relation.get('join_type', self.default_join_type)
            from_table = relation.get('from_table')
            to_table = relation.get('to_table')
            from_column = relation.get('from_column')
            to_column = relation.get('to_column')
            
            join = f"{join_type.upper()} JOIN {to_table} ON {from_table}.{from_column} = {to_table}.{to_column}"
            joins.append(join)
        
        return ' '.join(joins)
    
    def _build_where_clause(self, additional_filters=None):
        """Construit la clause WHERE"""
        conditions = []
        
        for filter_def in self.default_filters:
            field = filter_def.get('field')
            operator = filter_def.get('operator')
            value = filter_def.get('value')
            conditions.append(self._format_condition(field, operator, value))
        
        if additional_filters:
            for filter_def in additional_filters:
                field = filter_def.get('field')
                operator = filter_def.get('operator')
                value = filter_def.get('value')
                conditions.append(self._format_condition(field, operator, value))
        
        if conditions:
            return f"WHERE {' AND '.join(conditions)}"
        return ""
    
    def _format_condition(self, field, operator, value):
        """Formate une condition WHERE"""
        operators = {
            'equals': '=',
            'not_equals': '!=',
            'greater_than': '>',
            'less_than': '<',
            'greater_or_equal': '>=',
            'less_or_equal': '<=',
        }
        
        op = operators.get(operator, operator)
        
        if value is None:
            return f"{field} IS NULL" if op == '=' else f"{field} IS NOT NULL"
        
        if isinstance(value, str):
            return f"{field} {op} '{value}'"
        
        return f"{field} {op} {value}"


# ============================================================================
# RELATIONS ENTRE FAITS
# ============================================================================

class FactRelationship(BaseModel):
    """
    Relation entre plusieurs tables de faits
    Pour les schémas galaxie et constellations
    """
    
    name = models.CharField('Nom de la relation', max_length=200)
    description = models.TextField('Description', blank=True)
    
    from_fact = models.ForeignKey(
        FactTable,
        on_delete=models.CASCADE,
        related_name='outgoing_relationships',
        verbose_name='Table de faits source'
    )
    to_fact = models.ForeignKey(
        FactTable,
        on_delete=models.CASCADE,
        related_name='incoming_relationships',
        verbose_name='Table de faits cible'
    )
    
    from_column = models.CharField('Colonne source', max_length=200)
    to_column = models.CharField('Colonne cible', max_length=200)
    
    relation_type = models.CharField(
        'Type de relation',
        max_length=20,
        choices=RELATION_TYPES,
        default='many_to_one'
    )
    join_type = models.CharField(
        'Type de jointure',
        max_length=20,
        choices=JOIN_TYPES,
        default='left'
    )
    
    is_enabled = models.BooleanField('Activée', default=True)
    cardinality = models.FloatField('Cardinalité estimée', default=1.0)
    
    objects = FactRelationshipManager()
    
    class Meta:
        db_table = 'fact_relationships'
        ordering = ['name']
        verbose_name = 'Relation entre faits'
        verbose_name_plural = 'Relations entre faits'
        unique_together = ['from_fact', 'to_fact', 'from_column', 'to_column']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['from_fact', 'to_fact']),
            models.Index(fields=['is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.from_fact.name} -> {self.to_fact.name})"


# ============================================================================
# HIÉRARCHIES DE DIMENSIONS
# ============================================================================

class DimensionHierarchy(BaseModel):
    """
    Hiérarchie dans une table de dimension
    """
    
    name = models.CharField('Nom de la hiérarchie', max_length=200)
    description = models.TextField('Description', blank=True)
    
    dimension_table = models.ForeignKey(
        DimensionTable,
        on_delete=models.CASCADE,
        related_name='hierarchies',
        verbose_name='Table de dimension'
    )
    
    levels = models.JSONField(
        'Niveaux',
        default=list,
        help_text="Liste ordonnée des niveaux de hiérarchie"
    )
    
    default_level = models.CharField('Niveau par défaut', max_length=100, blank=True)
    is_active = models.BooleanField('Active', default=True)
    rollup_enabled = models.BooleanField('Rollup activé', default=True)
    drilldown_enabled = models.BooleanField('Drilldown activé', default=True)
    
    class Meta:
        db_table = 'dimension_hierarchies'
        ordering = ['name']
        verbose_name = 'Hiérarchie de dimension'
        verbose_name_plural = 'Hiérarchies de dimensions'
        unique_together = ['dimension_table', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.dimension_table.name})"
    
    @property
    def level_count(self):
        return len(self.levels) if self.levels else 0


# ============================================================================
# CALCULS PERSONNALISÉS
# ============================================================================

class CustomCalculation(BaseModel):
    """
    Calcul personnalisé pour les schémas dimensionnels
    """
    
    name = models.CharField('Nom du calcul', max_length=200)
    description = models.TextField('Description', blank=True)
    calculation_type = models.CharField(
        'Type de calcul',
        max_length=20,
        choices=CALCULATION_TYPES,
        default='direct'
    )
    
    dimensional_schema = models.ForeignKey(  # ← Renommé
        DimensionalSchema,
        on_delete=models.CASCADE,
        related_name='custom_calculations',
        verbose_name='Schéma dimensionnel'
    )
    
    formula = models.TextField(
        'Formule',
        validators=[validate_calculation_formula],
        help_text="Formule de calcul (ex: 'montant / quantite')"
    )
    
    result_column = models.CharField('Colonne résultat', max_length=200)
    result_type = models.CharField('Type du résultat', max_length=50, default='decimal')
    format_string = models.CharField('Format d\'affichage', max_length=50, blank=True)
    unit = models.CharField('Unité', max_length=50, blank=True)
    decimal_places = models.IntegerField('Décimales', default=2)
    
    is_active = models.BooleanField('Actif', default=True)
    tags = models.JSONField('Tags', default=list, blank=True)
    
    class Meta:
        db_table = 'custom_calculations'
        ordering = ['name']
        verbose_name = 'Calcul personnalisé'
        verbose_name_plural = 'Calculs personnalisés'
        unique_together = ['dimensional_schema', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['dimensional_schema', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.dimensional_schema.name})"
    
    def evaluate(self, row):
        try:
            context = {k: v for k, v in row.items()}
            return eval(self.formula, {"__builtins__": {}}, context)
        except Exception:
            return None


# ============================================================================
# SCHÉMAS DE GALAXIE
# ============================================================================

class GalaxySchema(BaseModel):
    """
    Schéma galaxie - Ensemble de schémas dimensionnels interconnectés
    """
    
    name = models.CharField('Nom de la galaxie', max_length=200)
    description = models.TextField('Description', blank=True)
    
    dimensional_schemas = models.ManyToManyField(  # ← Renommé
        DimensionalSchema,
        related_name='galaxy_schemas',
        verbose_name='Schémas dimensionnels'
    )
    
    galaxy_relationships = models.JSONField(
        'Relations entre schémas',
        default=list,
        blank=True
    )
    
    schema_graph = models.JSONField(
        'Graphe des schémas',
        default=dict,
        blank=True,
        validators=[validate_schema_graph]
    )
    
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='galaxy_schemas',
        verbose_name='Propriétaire'
    )
    tags = models.JSONField('Tags', default=list, blank=True)
    
    class Meta:
        db_table = 'galaxy_schemas'
        ordering = ['name']
        verbose_name = 'Schéma galaxie'
        verbose_name_plural = 'Schémas galaxie'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.dimensional_schemas.count()} schémas)"
    
    @property
    def dimensional_schema_count(self):
        return self.dimensional_schemas.count()
    
    def generate_unified_query(self):
        queries = []
        for schema in self.dimensional_schemas.all():
            queries.append(schema.generate_query())
        return " UNION ALL ".join(queries)
