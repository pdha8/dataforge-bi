```markdown
# ⭐ Star Schema Module Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Models](#core-models)
4. [Schema Types](#schema-types)
5. [API Endpoints](#api-endpoints)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Le module **Star Schema** est une extension avancée de la plateforme Sotifibre BI qui permet la modélisation dimensionnelle sophistiquée. Il offre :

- **Schémas en étoile (Star Schema)** : Modélisation classique avec une table de faits et plusieurs dimensions
- **Schémas en flocon (Snowflake Schema)** : Dimensions normalisées avec sous-dimensions
- **Schémas galaxie (Galaxy Schema)** : Multiples tables de faits partageant des dimensions communes
- **Hiérarchies de dimensions** : Navigation hiérarchique (Pays → Région → Ville)
- **Calculs personnalisés** : Formules métier avancées
- **Relations entre faits** : Connexion entre plusieurs tables de faits

### Fonctionnalités Clés

| Fonctionnalité | Description |
|----------------|-------------|
| **Modélisation dimensionnelle** | Support complet des schémas étoile, flocon et galaxie |
| **Hiérarchies** | Navigation en drill-down et roll-up |
| **Calculs avancés** | Formules personnalisées, ratios, tendances |
| **Relations entre faits** | Connexion de plusieurs tables de faits |
| **Cache intelligent** | Mise en cache automatique des requêtes |
| **Optimisation des performances** | Agrégations pré-calculées, index intelligents |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Star Schema Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              DimensionalSchema (Schéma principal)        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Fact Tables │  │ Dim Tables  │  │  Measures   │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ DimensionHier- │  │ FactRelation-   │  │ CustomCalcu-    │ │
│  │ archy          │  │ ship            │  │ lation          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              GalaxySchema (Constellation)               │   │
│  │         Regroupe plusieurs DimensionalSchema            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Models

### 1. DimensionalSchema
Modèle principal pour les schémas dimensionnels.

```python
class DimensionalSchema(BaseModel):
    name = models.CharField(max_length=200)                    # Nom du schéma
    description = models.TextField(blank=True)                 # Description
    schema_type = models.CharField(max_length=20)              # Type: star, snowflake, galaxy
    status = models.CharField(max_length=20)                   # Statut: draft, active, archived
    
    # Tables
    fact_tables = models.ManyToManyField(FactTable)           # Tables de faits
    dimension_tables = models.ManyToManyField(DimensionTable) # Tables de dimensions
    measures = models.ManyToManyField(Measure)                # Mesures
    
    # Configuration
    dimension_mapping = models.JSONField()                    # Mapping des dimensions
    relationships = models.JSONField()                        # Relations entre tables
    calculations = models.JSONField()                         # Calculs personnalisés
    default_filters = models.JSONField()                      # Filtres par défaut
    
    # Métadonnées
    grain = models.CharField(max_length=20)                   # Granularité
    default_join_type = models.CharField(max_length=20)       # Type de jointure par défaut
    
    # Performance
    query_count = models.IntegerField(default=0)              # Nombre de requêtes
    avg_query_time_ms = models.FloatField(default=0)          # Temps moyen de requête
    is_cached = models.BooleanField(default=False)            # Cache activé
    cache_ttl_seconds = models.IntegerField(default=300)      # Durée du cache
```

**Exemple :**
```python
from apps.star_schema.models import DimensionalSchema
from apps.data_warehouse.models import FactTable, DimensionTable, Measure

# Création d'un schéma en étoile pour l'analyse des ventes
ventes_schema = DimensionalSchema.objects.create(
    name="Analyse des Ventes",
    description="Schéma pour l'analyse des ventes par produit et par date",
    schema_type="star",
    status="active",
    grain="daily",
    default_join_type="left",
    dimension_mapping={
        "dim_date": ["annee", "mois", "jour"],
        "dim_produit": ["nom_produit", "categorie"]
    },
    is_cached=True,
    cache_ttl_seconds=600
)

# Ajout des tables
ventes_schema.fact_tables.add(fact_ventes)
ventes_schema.dimension_tables.add(dim_date, dim_produit)
ventes_schema.measures.add(measure_ca, measure_quantite)
```

### 2. DimensionHierarchy
Hiérarchies dans les tables de dimensions.

```python
class DimensionHierarchy(BaseModel):
    name = models.CharField(max_length=200)                   # Nom de la hiérarchie
    description = models.TextField(blank=True)                # Description
    dimension_table = models.ForeignKey(DimensionTable)       # Table de dimension
    levels = models.JSONField(default=list)                   # Niveaux de la hiérarchie
    default_level = models.CharField(max_length=100)          # Niveau par défaut
    is_active = models.BooleanField(default=True)             # Active ?
    rollup_enabled = models.BooleanField(default=True)        # Rollup activé ?
    drilldown_enabled = models.BooleanField(default=True)     # Drilldown activé ?
```

**Exemple :**
```python
# Hiérarchie géographique pour la dimension client
hierarchie_geo = DimensionHierarchy.objects.create(
    name="Hiérarchie Géographique",
    description="Pays → Région → Ville",
    dimension_table=dim_client,
    levels=["pays", "region", "ville"],
    default_level="region",
    is_active=True,
    rollup_enabled=True,
    drilldown_enabled=True
)
```

### 3. FactRelationship
Relations entre plusieurs tables de faits.

```python
class FactRelationship(BaseModel):
    name = models.CharField(max_length=200)                   # Nom de la relation
    description = models.TextField(blank=True)                # Description
    from_fact = models.ForeignKey(FactTable)                  # Table source
    to_fact = models.ForeignKey(FactTable)                    # Table cible
    from_column = models.CharField(max_length=200)            # Colonne source
    to_column = models.CharField(max_length=200)              # Colonne cible
    relation_type = models.CharField(max_length=20)           # Type de relation
    join_type = models.CharField(max_length=20)               # Type de jointure
    is_enabled = models.BooleanField(default=True)            # Activée ?
    cardinality = models.FloatField(default=1.0)              # Cardinalité estimée
```

**Exemple :**
```python
# Relation entre ventes et retours
relation_ventes_retours = FactRelationship.objects.create(
    name="Ventes → Retours",
    description="Relation entre les ventes et les retours",
    from_fact=fact_ventes,
    to_fact=fact_retours,
    from_column="transaction_id",
    to_column="transaction_id",
    relation_type="one_to_one",
    join_type="left",
    is_enabled=True,
    cardinality=1.0
)
```

### 4. CustomCalculation
Calculs personnalisés pour les schémas dimensionnels.

```python
class CustomCalculation(BaseModel):
    name = models.CharField(max_length=200)                   # Nom du calcul
    description = models.TextField(blank=True)                # Description
    calculation_type = models.CharField(max_length=20)        # Type de calcul
    dimensional_schema = models.ForeignKey(DimensionalSchema) # Schéma associé
    formula = models.TextField()                              # Formule de calcul
    result_column = models.CharField(max_length=200)          # Colonne résultat
    result_type = models.CharField(max_length=50)             # Type du résultat
    format_string = models.CharField(max_length=50)           # Format d'affichage
    unit = models.CharField(max_length=50, blank=True)        # Unité
    decimal_places = models.IntegerField(default=2)           # Décimales
    is_active = models.BooleanField(default=True)             # Actif ?
```

**Exemple :**
```python
# Calcul du panier moyen
panier_moyen = CustomCalculation.objects.create(
    name="Panier Moyen",
    description="Montant total / Nombre de transactions",
    calculation_type="ratio",
    dimensional_schema=ventes_schema,
    formula="montant_total / nb_transactions",
    result_column="panier_moyen",
    result_type="decimal",
    format_string="€#,##0.00",
    unit="EUR",
    decimal_places=2,
    is_active=True
)

# Calcul du taux de marge
taux_marge = CustomCalculation.objects.create(
    name="Taux de Marge",
    description="(CA - Coût) / CA * 100",
    calculation_type="percentage",
    dimensional_schema=ventes_schema,
    formula="(ca_total - cout_total) / ca_total * 100",
    result_column="taux_marge",
    result_type="percentage",
    format_string="#,##0.00",
    unit="%",
    decimal_places=2,
    is_active=True
)
```

### 5. GalaxySchema
Regroupement de plusieurs schémas dimensionnels.

```python
class GalaxySchema(BaseModel):
    name = models.CharField(max_length=200)                   # Nom de la galaxie
    description = models.TextField(blank=True)                # Description
    dimensional_schemas = models.ManyToManyField(DimensionalSchema)  # Schémas composants
    galaxy_relationships = models.JSONField(default=list)     # Relations entre schémas
    schema_graph = models.JSONField(default=dict)             # Graphe des schémas
    status = models.CharField(max_length=20)                  # Statut
    owner = models.ForeignKey(User, on_delete=models.SET_NULL) # Propriétaire
    tags = models.JSONField(default=list)                     # Tags
```

**Exemple :**
```python
# Création d'une galaxie pour l'analyse commerciale
galaxie_commerciale = GalaxySchema.objects.create(
    name="Analyse Commerciale Complète",
    description="Galaxie regroupant ventes, retours et stock",
    status="active",
    owner=admin_user
)

# Ajout des schémas
galaxie_commerciale.dimensional_schemas.add(ventes_schema, retours_schema, stock_schema)
```

---

## Schema Types

### 1. Star Schema (Étoile)
Structure classique avec une table de faits et plusieurs dimensions.

```
                    ┌─────────────────────┐
                    │   dim_date          │
                    │  ┌───────────────┐  │
                    │  │ date_id (PK)  │  │
                    │  │ annee         │  │
                    │  │ mois          │  │
                    │  │ jour          │  │
                    │  └───────────────┘  │
                    └──────────┬──────────┘
                               │
┌──────────────────┐           │           ┌──────────────────┐
│  dim_produit     │           │           │  dim_client      │
│ ┌─────────────┐  │           │           │ ┌─────────────┐  │
│ │produit_id(PK)│ │           │           │ │client_id(PK)│  │
│ │nom_produit  │  │           │           │ │nom_client   │  │
│ │categorie    │  │           │           │ │segment      │  │
│ └─────────────┘  │           │           │ └─────────────┘  │
└────────┬─────────┘           │           └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ventes_fait       │
                    │  ┌───────────────┐  │
                    │  │ date_id (FK)  │  │
                    │  │ produit_id(FK)│  │
                    │  │ client_id(FK) │  │
                    │  │ montant       │  │
                    │  │ quantite      │  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

### 2. Snowflake Schema (Flocon)
Dimensions normalisées avec sous-dimensions.

```
┌──────────────────┐
│  dim_produit     │
│ ┌─────────────┐  │
│ │produit_id(PK)│ │
│ │nom_produit  │  │
│ │categorie_id │──┼──────┐
│ └─────────────┘  │      │
└──────────────────┘      │
                           ▼
                  ┌──────────────────┐
                  │  dim_categorie   │
                  │ ┌─────────────┐  │
                  │ │categorie_id(PK)│
                  │ │nom_categorie │  │
                  │ │sous_categorie│  │
                  │ └─────────────┘  │
                  └──────────────────┘
```

### 3. Galaxy Schema (Galaxie)
Multiples tables de faits partageant des dimensions.

```
        dim_date ◄─────────┐
                           │
┌──────────────────┐       │       ┌──────────────────┐
│   ventes_fait    │       │       │   retours_fait   │
│ ┌─────────────┐  │       │       │ ┌─────────────┐  │
│ │ date_id (FK)│──┼───────┘       │ │ date_id (FK)│──┼──────┐
│ │ produit_id  │──┼───────┐       │ │ produit_id  │──┼──────┐
│ │ montant     │  │       │       │ │ montant     │  │      │
│ └─────────────┘  │       │       │ └─────────────┘  │      │
└──────────────────┘       │       └──────────────────┘      │
                           │                                │
                           ▼                                ▼
                  ┌──────────────────────────────────────────┐
                  │              dim_produit                 │
                  │ ┌────────────────────────────────────┐  │
                  │ │ produit_id (PK)                    │  │
                  │ │ nom_produit                        │  │
                  │ │ categorie                          │  │
                  │ └────────────────────────────────────┘  │
                  └──────────────────────────────────────────┘
```

---

## API Endpoints

### Dimensional Schemas
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/star-schema/dimensional-schemas/` | Liste tous les schémas dimensionnels |
| POST | `/api/star-schema/dimensional-schemas/` | Crée un schéma dimensionnel |
| GET | `/api/star-schema/dimensional-schemas/{id}/` | Détails d'un schéma |
| PUT | `/api/star-schema/dimensional-schemas/{id}/` | Met à jour un schéma |
| DELETE | `/api/star-schema/dimensional-schemas/{id}/` | Supprime un schéma |
| POST | `/api/star-schema/dimensional-schemas/{id}/execute/` | Exécute le schéma |
| GET | `/api/star-schema/dimensional-schemas/{id}/sql/` | Génère le SQL |
| POST | `/api/star-schema/dimensional-schemas/{id}/validate/` | Valide la configuration |
| POST | `/api/star-schema/dimensional-schemas/{id}/clear-cache/` | Vide le cache |
| GET | `/api/star-schema/dimensional-schemas/stats/` | Statistiques globales |

### Dimension Hierarchies
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/star-schema/dimension-hierarchies/` | Liste les hiérarchies |
| POST | `/api/star-schema/dimension-hierarchies/` | Crée une hiérarchie |
| GET | `/api/star-schema/dimension-hierarchies/{id}/` | Détails d'une hiérarchie |

### Fact Relationships
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/star-schema/fact-relationships/` | Liste les relations |
| POST | `/api/star-schema/fact-relationships/` | Crée une relation |
| GET | `/api/star-schema/fact-relationships/{id}/` | Détails d'une relation |

### Custom Calculations
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/star-schema/calculations/` | Liste les calculs |
| POST | `/api/star-schema/calculations/` | Crée un calcul |
| GET | `/api/star-schema/calculations/{id}/` | Détails d'un calcul |

### Galaxy Schemas
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/star-schema/galaxies/` | Liste les galaxies |
| POST | `/api/star-schema/galaxies/` | Crée une galaxie |
| GET | `/api/star-schema/galaxies/{id}/` | Détails d'une galaxie |
| POST | `/api/star-schema/galaxies/{id}/execute-unified/` | Exécute la galaxie |
| GET | `/api/star-schema/galaxies/{id}/unified-sql/` | Génère le SQL unifié |

---

## Usage Examples

### 1. Créer un schéma en étoile complet

```python
from apps.star_schema.models import DimensionalSchema
from apps.data_warehouse.models import FactTable, DimensionTable, Measure

# Étape 1: Créer les tables dans le data warehouse
# Table des faits
fact_ventes = FactTable.objects.create(
    name="ventes_fait",
    schema=schema_ventes,
    description="Ventes quotidiennes",
    granularity="daily"
)

# Tables de dimension
dim_date = DimensionTable.objects.create(
    name="dim_date",
    schema=schema_ventes,
    description="Dimension date",
    dimension_type="conformed"
)

dim_produit = DimensionTable.objects.create(
    name="dim_produit",
    schema=schema_ventes,
    description="Dimension produit",
    dimension_type="slowly_changing",
    scd_type="type2"
)

# Mesures
measure_ca = Measure.objects.create(
    fact_table=fact_ventes,
    name="Chiffre d'Affaires",
    column="montant",
    aggregation_type="sum",
    unit="EUR"
)

# Étape 2: Créer le schéma en étoile
schema_ventes = DimensionalSchema.objects.create(
    name="Analyse des Ventes",
    description="Schéma pour l'analyse des ventes",
    schema_type="star",
    status="active",
    grain="daily",
    dimension_mapping={
        "dim_date": ["annee", "mois", "jour"],
        "dim_produit": ["nom_produit", "categorie"]
    },
    is_cached=True,
    cache_ttl_seconds=600
)

# Ajouter les tables
schema_ventes.fact_tables.add(fact_ventes)
schema_ventes.dimension_tables.add(dim_date, dim_produit)
schema_ventes.measures.add(measure_ca)
```

### 2. Créer une hiérarchie de dimension

```python
from apps.star_schema.models import DimensionHierarchy

# Hiérarchie géographique
hierarchie_geo = DimensionHierarchy.objects.create(
    name="Hiérarchie Géographique",
    description="Pays → Région → Ville",
    dimension_table=dim_client,
    levels=["pays", "region", "ville"],
    default_level="region",
    is_active=True,
    rollup_enabled=True,
    drilldown_enabled=True
)

# Hiérarchie temporelle
hierarchie_temporelle = DimensionHierarchy.objects.create(
    name="Hiérarchie Temporelle",
    description="Année → Trimestre → Mois → Jour",
    dimension_table=dim_date,
    levels=["annee", "trimestre", "mois", "jour"],
    default_level="mois",
    is_active=True,
    rollup_enabled=True,
    drilldown_enabled=True
)
```

### 3. Exécuter un schéma via API

```bash
# Générer le SQL
curl -X GET "http://localhost:8000/api/star-schema/dimensional-schemas/{id}/sql/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Exécuter le schéma
curl -X POST "http://localhost:8000/api/star-schema/dimensional-schemas/{id}/execute/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"annee": 2024, "categorie": "electronique"},
    "limit": 100,
    "format": "json"
  }'

# Exporter en CSV
curl -X POST "http://localhost:8000/api/star-schema/dimensional-schemas/{id}/execute/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"annee": 2024},
    "format": "csv"
  }' \
  --output analyse_ventes.csv
```

### 4. Créer une galaxie de schémas

```python
from apps.star_schema.models import GalaxySchema

# Créer les schémas individuels
schema_ventes = DimensionalSchema.objects.get(name="Analyse des Ventes")
schema_retours = DimensionalSchema.objects.get(name="Analyse des Retours")
schema_stock = DimensionalSchema.objects.get(name="Analyse du Stock")

# Créer la galaxie
galaxie = GalaxySchema.objects.create(
    name="Analyse Commerciale Complète",
    description="Galaxie regroupant ventes, retours et stock",
    status="active",
    owner=admin_user,
    galaxy_relationships=[
        {
            "from_schema": "Analyse des Ventes",
            "to_schema": "Analyse des Retours",
            "relationship": "ventes → retours"
        },
        {
            "from_schema": "Analyse des Ventes",
            "to_schema": "Analyse du Stock",
            "relationship": "ventes → stock"
        }
    ]
)

# Ajouter les schémas
galaxie.dimensional_schemas.add(schema_ventes, schema_retours, schema_stock)

# Exécuter la galaxie complète
result = galaxy_service.execute_unified()
```

---

## Best Practices

### 1. Conventions de nommage

| Type | Convention | Exemple |
|------|------------|---------|
| Schéma dimensionnel | `{domaine}_{analyse}` | `ventes_analyse` |
| Hiérarchie | `{dimension}_{type}_hierarchy` | `date_temporal_hierarchy` |
| Relation | `{from}_{to}_relationship` | `ventes_retours_relationship` |
| Calcul | `{measure}_{type}_calc` | `ca_moyen_calc` |

### 2. Optimisation des performances

```python
# Activer le cache pour les schémas fréquemment utilisés
schema.is_cached = True
schema.cache_ttl_seconds = 3600  # 1 heure

# Utiliser des agrégations pré-calculées
from apps.data_warehouse.models import AggregationTable

aggregation = AggregationTable.objects.create(
    name="ventes_daily_agg",
    base_table=fact_ventes,
    granularity="daily",
    group_by_columns=["date_id", "produit_id"],
    aggregated_columns=["SUM(montant) as total_ventes"],
    refresh_frequency="hourly"
)
```

### 3. Gestion des hiérarchies

```python
# Activer le drill-down
hierarchy.drilldown_enabled = True

# Activer le roll-up pour les agrégations
hierarchy.rollup_enabled = True

# Définir un niveau par défaut
hierarchy.default_level = "mois"
```

### 4. Validation des calculs

```python
# Valider la formule avant de l'activer
calculation.is_active = False
calculation.save()

# Tester la formule
test_data = {"montant": 100, "quantite": 10}
result = calculation.evaluate(test_data)

if result is not None:
    calculation.is_active = True
    calculation.save()
```

---

## Performance Optimization

### 1. Cache Strategy

```python
# Cache par schéma
schema.is_cached = True
schema.cache_ttl_seconds = 600  # 10 minutes

# Invalidation automatique du cache
@receiver(post_save, sender=FactTable)
def invalidate_schema_cache(sender, instance, **kwargs):
    from django.core.cache import cache
    for schema in instance.dimensional_schemas.all():
        cache.delete_pattern(f"dimensional_schema_{schema.id}_*")
```

### 2. Query Optimization

```sql
-- SQL généré optimisé avec hints
SELECT /*+ PARALLEL(4) */
    dim_date.annee,
    dim_produit.categorie,
    SUM(ventes_fait.montant) as total_ventes,
    AVG(ventes_fait.montant) as montant_moyen
FROM ventes_fait
LEFT JOIN dim_date ON ventes_fait.date_id = dim_date.date_id
LEFT JOIN dim_produit ON ventes_fait.produit_id = dim_produit.produit_id
WHERE dim_date.annee = 2024
GROUP BY dim_date.annee, dim_produit.categorie
```

### 3. Monitoring

```python
# Suivi des performances
from apps.star_schema.models import DimensionalSchema

slow_schemas = DimensionalSchema.objects.filter(
    avg_query_time_ms__gt=5000
).order_by('-avg_query_time_ms')

for schema in slow_schemas:
    print(f"Schema lent: {schema.name} - {schema.avg_query_time_ms}ms")
    print(f"Requêtes: {schema.query_count}")
    print(f"Status: {schema.status}")
```

---

## Troubleshooting

### Problèmes courants et solutions

| Problème | Solution |
|----------|----------|
| Requête lente | Activer le cache, créer des agrégations, optimiser les index |
| Résultats incorrects | Valider les mappings, vérifier les formules de calcul |
| Cache non vidé | Utiliser `clear_cache()` après les mises à jour |
| Hiérarchie non fonctionnelle | Vérifier les niveaux, activer drilldown/rollup |

### Débogage

```python
# Activer les logs de débogage
import logging
logging.getLogger('apps.star_schema').setLevel(logging.DEBUG)

# Vérifier le SQL généré
sql = schema.generate_query()
print(sql)

# Valider la configuration
validation = schema_service.validate()
print(f"Valid: {validation['valid']}")
print(f"Errors: {validation['errors']}")
print(f"Warnings: {validation['warnings']}")

# Vérifier les relations
for rel in FactRelationship.objects.all():
    print(f"{rel.name}: {rel.from_fact.name} → {rel.to_fact.name}")
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-10 | Version initiale avec DimensionalSchema, GalaxySchema, hiérarchies et calculs |
```

Cette documentation est à sauvegarder dans :
```
/home/user/sotifibre/sotifibre_backend_django/docs/modules/star_schema.md
```