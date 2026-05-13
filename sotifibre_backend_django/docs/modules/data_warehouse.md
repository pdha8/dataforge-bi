```markdown
# 📊 Documentation du Module Data Warehouse

## Table des Matières
1. [Présentation Générale](#présentation-générale)
2. [Architecture](#architecture)
3. [Modèles Principaux](#modèles-principaux)
4. [Schéma en Étoile (Star Schema)](#schéma-en-étoile-star-schema)
5. [Endpoints API](#endpoints-api)
6. [Exemples d'Utilisation](#exemples-dutilisation)
7. [Bonnes Pratiques](#bonnes-pratiques)
8. [Optimisation des Performances](#optimisation-des-performances)
9. [Dépannage](#dépannage)

---

## Présentation Générale

Le module **Data Warehouse** est le système de stockage analytique central de la plateforme BI Sotifibre. Il permet de :

- **Modélisation dimensionnelle** : Support des schémas en étoile, faits et dimensions
- **Gestion des agrégations** : Tables pré-agrégées pour l'optimisation des performances
- **Gestion des métadonnées** : Définitions complètes des schémas, tables et colonnes
- **Monitoring des performances** : Métriques des requêtes, statistiques des tables, suivi des rafraîchissements
- **Piste d'audit** : Journalisation complète de toutes les opérations

### Fonctionnalités Clés

| Fonctionnalité | Description |
|----------------|-------------|
| **Schémas en étoile** | Modélisation dimensionnelle pour l'analyse BI |
| **Dimensions à évolution lente (SCD)** | Support des stratégies SCD Type 0 à 6 |
| **Partitionnement** | Stratégies de partitionnement par plage, liste ou hash |
| **Compression** | Compression au niveau table pour l'optimisation du stockage |
| **Planification des rafraîchissements** | Rafraîchissement automatique avec expressions CRON |
| **Métriques de performance** | Temps de requête, lignes analysées, taux de cache |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Couche Data Warehouse                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Schémas   │  │   Tables    │  │   Schémas en        │  │
│  │ (Conteneurs)│  │ (Faits/Dims)│  │   Étoile            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Mesures    │  │ Attributs   │  │   Agrégations       │  │
│  │   (KPIs)    │  │  (Détails)  │  │   (Pré-calculées)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │      Monitoring & Journalisation (Métriques/Logs)   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Modèles Principaux

### 1. DataWarehouseSchema
Conteneur pour organiser les tables du data warehouse.

```python
class DataWarehouseSchema(BaseModel):
    name = models.CharField(max_length=100, unique=True)          # Nom du schéma
    description = models.TextField()                               # Description
    default_tablespace = models.CharField(max_length=100)         # Tablespace par défaut
    default_compression = models.BooleanField(default=False)      # Compression par défaut
    tags = models.JSONField(default=dict)                         # Tags
    is_active = models.BooleanField(default=True)                 # Actif ?
    table_count = models.IntegerField(default=0)                  # Nombre de tables
    size_bytes = models.BigIntegerField(default=0)                # Taille totale
    last_analyzed = models.DateTimeField(null=True)               # Dernière analyse
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Propriétaire
```

**Exemple :**
```python
# Création d'un schéma de ventes
schema = DataWarehouseSchema.objects.create(
    name="ventes_dw",
    description="Schéma Data Warehouse des ventes",
    default_tablespace="ts_ventes",
    default_compression=True,
    owner=admin_user
)
```

### 2. DataWarehouseTable
Modèle de base pour toutes les tables du data warehouse.

```python
class DataWarehouseTable(BaseModel):
    # Informations de base
    name = models.CharField(max_length=200)                       # Nom de la table
    table_type = models.CharField(max_length=20, choices=TABLE_TYPES)  # Type de table
    description = models.TextField()                               # Description
    status = models.CharField(max_length=20, choices=TABLE_STATUS) # Statut
    
    # Schéma
    schema = models.ForeignKey(DataWarehouseSchema, on_delete=models.CASCADE)
    
    # Structure
    columns = models.JSONField(default=list)                       # Colonnes
    primary_key = models.JSONField(default=list)                   # Clé primaire
    foreign_keys = models.JSONField(default=list)                  # Clés étrangères
    indexes = models.JSONField(default=list)                       # Index
    
    # Partitionnement
    is_partitioned = models.BooleanField(default=False)            # Partitionnée ?
    partition_column = models.CharField(max_length=200, blank=True) # Colonne de partition
    partition_type = models.CharField(max_length=20, choices=PARTITION_TYPES, blank=True)
    
    # Statistiques
    row_count = models.BigIntegerField(default=0)                  # Nombre de lignes
    size_bytes = models.BigIntegerField(default=0)                 # Taille en octets
    
    # Rafraîchissement
    refresh_frequency = models.CharField(max_length=20, choices=REFRESH_FREQUENCIES)  # Fréquence
    last_refresh = models.DateTimeField(null=True)                 # Dernier rafraîchissement
    next_refresh = models.DateTimeField(null=True)                 # Prochain rafraîchissement
```

### 3. FactTable (Table des faits)
Table spécialisée pour stocker les faits/mesures métier.

```python
class FactTable(DataWarehouseTable):
    granularity = models.CharField(max_length=20, choices=GRANULARITIES)  # Granularité
    measures = models.ManyToManyField(Measure, related_name='fact_tables')
```

**Exemple :**
```python
# Création d'une table de faits des ventes
fact_table = FactTable.objects.create(
    name="ventes_fait",
    table_type="fact",
    schema=schema_ventes,
    description="Transactions de ventes quotidiennes",
    granularity="daily",
    columns=[
        {"name": "date_id", "type": "date", "nullable": False},
        {"name": "produit_id", "type": "bigint", "nullable": False},
        {"name": "client_id", "type": "bigint", "nullable": False},
        {"name": "montant", "type": "decimal(18,2)", "nullable": False},
        {"name": "quantite", "type": "integer", "nullable": False}
    ],
    primary_key=["date_id", "produit_id", "client_id"],
    row_count=1000000,
    refresh_frequency="daily"
)
```

### 4. DimensionTable (Table de dimension)
Table spécialisée pour stocker les attributs descriptifs.

```python
class DimensionTable(DataWarehouseTable):
    dimension_type = models.CharField(max_length=20, choices=DIMENSION_TYPES)  # Type de dimension
    scd_type = models.CharField(max_length=10, choices=SCD_TYPES, blank=True)  # Type SCD
```

**Exemple :**
```python
# Création d'une dimension produit avec SCD Type 2
produit_dim = DimensionTable.objects.create(
    name="dim_produit",
    table_type="dimension",
    schema=schema_ventes,
    description="Dimension produit avec SCD Type 2",
    dimension_type="slowly_changing",
    scd_type="type2",
    columns=[
        {"name": "produit_id", "type": "bigint", "nullable": False},
        {"name": "nom_produit", "type": "varchar(200)", "nullable": False},
        {"name": "categorie", "type": "varchar(100)"},
        {"name": "prix", "type": "decimal(10,2)"},
        {"name": "valide_du", "type": "date"},
        {"name": "valide_au", "type": "date"},
        {"name": "est_courant", "type": "boolean"}
    ],
    primary_key=["produit_id", "valide_du"],
    row_count=5000,
    refresh_frequency="weekly"
)
```

### 5. Measure (Mesure)
Indicateurs/KPIs métier associés aux tables de faits.

```python
class Measure(BaseModel):
    fact_table = models.ForeignKey(FactTable, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)                        # Nom
    column = models.CharField(max_length=200)                      # Colonne source
    aggregation_type = models.CharField(max_length=20, choices=AGGREGATION_TYPES)  # Type d'agrégation
    alias = models.CharField(max_length=200, blank=True)           # Alias
    description = models.TextField(blank=True)                     # Description
    is_calculated = models.BooleanField(default=False)             # Mesure calculée ?
    formula = models.TextField(blank=True)                         # Formule
    format_string = models.CharField(max_length=50, blank=True)    # Format d'affichage
    unit = models.CharField(max_length=50, blank=True)             # Unité
    decimal_places = models.IntegerField(default=2)                # Nombre de décimales
    tags = models.JSONField(default=list, blank=True)              # Tags
    is_active = models.BooleanField(default=True)                  # Active ?
```

**Exemple :**
```python
# Création des mesures pour la table de faits des ventes
ventes_totales = Measure.objects.create(
    fact_table=ventes_fait,
    name="Ventes Totales",
    column="montant",
    aggregation_type="sum",
    alias="ca_total",
    format_string="€#,##0.00",
    unit="EUR",
    decimal_places=2
)

quantite_totale = Measure.objects.create(
    fact_table=ventes_fait,
    name="Quantité Totale",
    column="quantite",
    aggregation_type="sum",
    alias="qte_totale",
    format_string="#,##0",
    unit="unités"
)

panier_moyen = Measure.objects.create(
    fact_table=ventes_fait,
    name="Panier Moyen",
    column="montant",
    aggregation_type="avg",
    alias="panier_moyen",
    format_string="€#,##0.00",
    unit="EUR",
    decimal_places=2
)
```

### 6. DimensionAttribute (Attribut de dimension)
Attributs individuels des tables de dimension.

```python
class DimensionAttribute(BaseModel):
    dimension_table = models.ForeignKey(DimensionTable, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)                        # Nom
    column = models.CharField(max_length=200)                      # Colonne
    data_type = models.CharField(max_length=20, choices=COLUMN_TYPES)  # Type de données
    description = models.TextField(blank=True)                     # Description
    is_key = models.BooleanField(default=False)                    # Clé de dimension ?
    is_hierarchical = models.BooleanField(default=False)           # Hiérarchique ?
    format_string = models.CharField(max_length=50, blank=True)    # Format d'affichage
    tags = models.JSONField(default=list, blank=True)              # Tags
    is_active = models.BooleanField(default=True)                  # Actif ?
    parent_attribute = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)  # Attribut parent
```

**Exemple :**
```python
# Création d'attributs hiérarchiques pour la dimension produit
categorie_attr = DimensionAttribute.objects.create(
    dimension_table=produit_dim,
    name="Catégorie",
    column="categorie",
    data_type="varchar",
    is_hierarchical=True
)

sous_categorie_attr = DimensionAttribute.objects.create(
    dimension_table=produit_dim,
    name="Sous-catégorie",
    column="sous_categorie",
    data_type="varchar",
    is_hierarchical=True,
    parent_attribute=categorie_attr
)

marque_attr = DimensionAttribute.objects.create(
    dimension_table=produit_dim,
    name="Marque",
    column="marque",
    data_type="varchar"
)
```

### 7. StarSchema (Schéma en étoile)
Modèle métier combinant faits et dimensions.

```python
class StarSchema(BaseModel):
    name = models.CharField(max_length=200)                        # Nom
    description = models.TextField(blank=True)                     # Description
    fact_table = models.ForeignKey(FactTable, on_delete=models.CASCADE)
    dimension_tables = models.ManyToManyField(DimensionTable)
    fact_columns = models.JSONField(default=list)                  # Colonnes de faits
    dimension_columns = models.JSONField(default=dict)             # Colonnes de dimensions
    relationships = models.JSONField(default=dict)                 # Relations
    tags = models.JSONField(default=list, blank=True)              # Tags
    is_active = models.BooleanField(default=True)                  # Actif ?
    query_count = models.IntegerField(default=0)                   # Nombre de requêtes
    last_queried_at = models.DateTimeField(null=True)              # Dernière requête
    avg_query_time_ms = models.FloatField(default=0)               # Temps moyen de requête
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Propriétaire
```

**Exemple :**
```python
# Création d'un schéma en étoile pour l'analyse des ventes
ventes_star = StarSchema.objects.create(
    name="Analyse des Ventes",
    description="Schéma en étoile pour l'analyse des ventes",
    fact_table=ventes_fait,
    fact_columns=["montant", "quantite"],
    dimension_columns={
        "dim_date": ["annee", "trimestre", "mois", "jour"],
        "dim_produit": ["nom_produit", "categorie", "marque"],
        "dim_client": ["segment", "region"]
    },
    owner=analyste_user
)

# Ajout des tables de dimension
ventes_star.dimension_tables.add(date_dim, produit_dim, client_dim)
```

### 8. AggregationTable (Table d'agrégation)
Tables pré-agrégées pour l'optimisation des performances.

```python
class AggregationTable(BaseModel):
    name = models.CharField(max_length=200)                        # Nom
    base_table = models.ForeignKey(DataWarehouseTable, on_delete=models.CASCADE)  # Table source
    granularity = models.CharField(max_length=20, choices=GRANULARITIES)  # Granularité
    group_by_columns = models.JSONField(default=list)              # Colonnes de groupement
    aggregated_columns = models.JSONField(default=list)            # Colonnes agrégées
    refresh_frequency = models.CharField(max_length=20, choices=REFRESH_FREQUENCIES)  # Fréquence
    last_refresh = models.DateTimeField(null=True)                 # Dernier rafraîchissement
    row_count = models.BigIntegerField(default=0)                  # Nombre de lignes
    size_bytes = models.BigIntegerField(default=0)                 # Taille en octets
    compression_ratio = models.FloatField(default=1.0)             # Taux de compression
```

**Exemple :**
```python
# Création d'une agrégation quotidienne pour accélérer les rapports
agregation_quotidienne = AggregationTable.objects.create(
    name="ventes_quotidien_agg",
    base_table=ventes_fait,
    granularity="daily",
    group_by_columns=["date_id"],
    aggregated_columns=[
        "SUM(montant) as total_ventes",
        "AVG(montant) as montant_moyen",
        "COUNT(*) as nb_transactions"
    ],
    refresh_frequency="hourly"
)
```

---

## Schéma en Étoile (Star Schema)

### Exemple : Schéma en Étoile des Ventes

```
                    ┌─────────────────────┐
                    │   dim_date          │
                    │  ┌───────────────┐  │
                    │  │ date_id (PK)  │  │
                    │  │ date          │  │
                    │  │ annee         │  │
                    │  │ trimestre     │  │
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
│ │marque       │  │           │           │ │region       │  │
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

### SQL Généré
```sql
SELECT 
    dim_date.annee,
    dim_produit.categorie,
    SUM(ventes_fait.montant) as total_ventes,
    AVG(ventes_fait.montant) as montant_moyen,
    SUM(ventes_fait.quantite) as quantite_totale
FROM ventes_fait
LEFT JOIN dim_date ON ventes_fait.date_id = dim_date.date_id
LEFT JOIN dim_produit ON ventes_fait.produit_id = dim_produit.produit_id
GROUP BY dim_date.annee, dim_produit.categorie
```

---

## Endpoints API

### Schémas
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/schemas/` | Liste tous les schémas |
| POST | `/api/data-warehouse/schemas/` | Crée un schéma |
| GET | `/api/data-warehouse/schemas/{id}/` | Détails d'un schéma |
| GET | `/api/data-warehouse/schemas/{id}/tables/` | Liste les tables d'un schéma |
| GET | `/api/data-warehouse/schemas/{id}/stats/` | Statistiques d'un schéma |

### Tables
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/tables/` | Liste toutes les tables |
| POST | `/api/data-warehouse/tables/` | Crée une table |
| POST | `/api/data-warehouse/tables/{id}/refresh/` | Rafraîchit une table |
| POST | `/api/data-warehouse/tables/{id}/analyze/` | Analyse une table |
| POST | `/api/data-warehouse/tables/{id}/optimize/` | Optimise une table |

### Tables de Faits
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/fact-tables/` | Liste les tables de faits |
| GET | `/api/data-warehouse/fact-tables/{id}/measures/` | Liste les mesures |
| POST | `/api/data-warehouse/fact-tables/{id}/add-measure/` | Ajoute une mesure |

### Tables de Dimension
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/dimensions/` | Liste les tables de dimension |
| GET | `/api/data-warehouse/dimensions/{id}/attributes/` | Liste les attributs |
| POST | `/api/data-warehouse/dimensions/{id}/add-attribute/` | Ajoute un attribut |

### Schémas en Étoile
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/star-schemas/` | Liste les schémas en étoile |
| POST | `/api/data-warehouse/star-schemas/` | Crée un schéma en étoile |
| POST | `/api/data-warehouse/star-schemas/{id}/execute/` | Exécute le schéma |
| GET | `/api/data-warehouse/star-schemas/{id}/sql/` | Récupère le SQL généré |

### Agrégations
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/aggregations/` | Liste les tables d'agrégation |
| POST | `/api/data-warehouse/aggregations/{id}/refresh/` | Rafraîchit une agrégation |

### Monitoring
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-warehouse/metrics/` | Liste les métriques |
| GET | `/api/data-warehouse/logs/` | Liste les logs |
| GET | `/api/data-warehouse/logs/stats/` | Statistiques des logs |

---

## Exemples d'Utilisation

### 1. Création Complète d'un Data Warehouse

```python
# Étape 1 : Création du schéma
schema_ventes = DataWarehouseSchema.objects.create(
    name="ventes_entrepot",
    description="Entrepôt de données des ventes",
    default_tablespace="ts_ventes",
    default_compression=True
)

# Étape 2 : Création des tables de dimension
date_dim = DimensionTable.objects.create(
    name="dim_date",
    schema=schema_ventes,
    description="Dimension date",
    dimension_type="conformed",
    columns=[
        {"name": "date_id", "type": "date", "nullable": False},
        {"name": "annee", "type": "integer"},
        {"name": "trimestre", "type": "integer"},
        {"name": "mois", "type": "integer"},
        {"name": "semaine", "type": "integer"},
        {"name": "jour", "type": "integer"}
    ],
    primary_key=["date_id"],
    refresh_frequency="monthly"
)

produit_dim = DimensionTable.objects.create(
    name="dim_produit",
    schema=schema_ventes,
    description="Dimension produit",
    dimension_type="slowly_changing",
    scd_type="type2",
    columns=[
        {"name": "produit_id", "type": "bigint", "nullable": False},
        {"name": "nom_produit", "type": "varchar(200)"},
        {"name": "categorie", "type": "varchar(100)"},
        {"name": "prix", "type": "decimal(10,2)"},
        {"name": "valide_du", "type": "date"},
        {"name": "valide_au", "type": "date"},
        {"name": "est_courant", "type": "boolean"}
    ],
    primary_key=["produit_id", "valide_du"],
    refresh_frequency="daily"
)

# Étape 3 : Création de la table de faits
ventes_fait = FactTable.objects.create(
    name="ventes_fait",
    schema=schema_ventes,
    description="Table de faits des ventes",
    granularity="daily",
    columns=[
        {"name": "date_id", "type": "date", "nullable": False},
        {"name": "produit_id", "type": "bigint", "nullable": False},
        {"name": "montant", "type": "decimal(18,2)", "nullable": False},
        {"name": "quantite", "type": "integer", "nullable": False}
    ],
    primary_key=["date_id", "produit_id"],
    refresh_frequency="daily"
)

# Étape 4 : Ajout des mesures
ca_total = Measure.objects.create(
    fact_table=ventes_fait,
    name="Chiffre d'Affaires Total",
    column="montant",
    aggregation_type="sum",
    alias="ca",
    format_string="€#,##0.00",
    unit="EUR",
    decimal_places=2
)

nb_ventes = Measure.objects.create(
    fact_table=ventes_fait,
    name="Nombre de Ventes",
    column="quantite",
    aggregation_type="count",
    alias="nb_ventes",
    format_string="#,##0",
    unit="transactions"
)

# Étape 5 : Création du schéma en étoile
ventes_etoile = StarSchema.objects.create(
    name="Analyse Commerciale",
    description="Schéma en étoile pour l'analyse des performances commerciales",
    fact_table=ventes_fait,
    fact_columns=["montant", "quantite"],
    dimension_columns={
        "dim_date": ["annee", "trimestre", "mois"],
        "dim_produit": ["nom_produit", "categorie"]
    },
    owner=utilisateur
)

ventes_etoile.dimension_tables.add(date_dim, produit_dim)
```

### 2. Exécution d'un Schéma en Étoile via API

```bash
# Récupération du SQL généré
curl -X GET "http://localhost:8000/api/data-warehouse/star-schemas/{id}/sql/" \
  -H "Authorization: Bearer VOTRE_TOKEN"

# Exécution du schéma en étoile
curl -X POST "http://localhost:8000/api/data-warehouse/star-schemas/{id}/execute/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100, "params": {"annee": 2024}}'
```

### 3. Rafraîchissement d'une Table

```bash
curl -X POST "http://localhost:8000/api/data-warehouse/tables/{id}/refresh/" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

### 4. Récupération des Métriques

```bash
curl -X GET "http://localhost:8000/api/data-warehouse/tables/{id}/metrics/?hours=24" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

### 5. Ajout d'un Attribut de Dimension

```python
# Ajout d'un attribut de dimension via API
import requests

response = requests.post(
    "http://localhost:8000/api/data-warehouse/dimensions/{id}/add-attribute/",
    headers={"Authorization": "Bearer VOTRE_TOKEN"},
    json={
        "name": "Marque",
        "column": "marque",
        "data_type": "varchar",
        "description": "Marque du produit",
        "is_key": False,
        "is_hierarchical": False
    }
)
```

---

## Bonnes Pratiques

### 1. Conventions de Nommage

| Type d'Objet | Préfixe | Exemple |
|--------------|---------|---------|
| Schéma | `{domaine}_dw` | `ventes_dw` |
| Table de faits | `{sujet}_fait` | `ventes_fait` |
| Table de dimension | `dim_{entite}` | `dim_produit` |
| Agrégation | `{sujet}_{granularite}_agg` | `ventes_quotidien_agg` |
| Schéma en étoile | `{sujet}_etoile` | `ventes_etoile` |

### 2. Nommage des Colonnes
- Utiliser le snake_case : `montant_commande`, `client_id`
- Inclure l'unité dans le nom : `montant_usd`, `poids_kg`
- Utiliser des suffixes : `_id` pour les clés étrangères, `_at` pour les timestamps

### 3. Stratégie de Partitionnement

```python
# Partitionnement par plage sur la date
if fact_table.granularity == "daily":
    fact_table.is_partitioned = True
    fact_table.partition_column = "date_id"
    fact_table.partition_type = "range"
```

### 4. Recommandations d'Index

```python
# Pour les tables de faits
indexes = [
    {"columns": ["date_id"], "type": "btree"},
    {"columns": ["produit_id"], "type": "btree"},
    {"columns": ["date_id", "produit_id"], "type": "btree"}
]

# Pour les tables de dimension
indexes = [
    {"columns": ["nom_produit"], "type": "btree"},
    {"columns": ["categorie"], "type": "btree"}
]
```

### 5. Stratégies de Rafraîchissement

| Type de Table | Fréquence Recommandée |
|---------------|----------------------|
| Petites dimensions | Hebdomadaire ou Mensuel |
| Grandes dimensions | Quotidien |
| Tables de faits | Quotidien ou Temps réel |
| Agrégations | Horaire ou Quotidien |

---

## Optimisation des Performances

### 1. Optimisation des Requêtes

```python
# Utilisation des schémas en étoile pour générer des requêtes optimisées
sql = star_schema.generate_query()

# Ajout d'indices pour l'optimiseur de requête
sql = f"""
SELECT /*+ PARALLEL(4) */
    {colonnes}
FROM {table_faits}
LEFT JOIN {tables_dimension}
WHERE {conditions}
"""

# Utilisation de vues matérialisées pour les agrégations complexes
CREATE MATERIALIZED VIEW ventes_mensuelles_agg AS
SELECT 
    date_trunc('month', date_id) as mois,
    produit_id,
    SUM(montant) as total_ventes,
    COUNT(*) as nb_transactions
FROM ventes_fait
GROUP BY date_trunc('month', date_id), produit_id
```

### 2. Surveillance des Requêtes Lentes

```python
# Suivi des requêtes lentes
from apps.data_warehouse.models import DataWarehouseMetric

requetes_lentes = DataWarehouseMetric.objects.filter(
    query_time_ms__gt=5000
).select_related('table')
```

### 3. Maintenance VACUUM et ANALYZE

```python
# Maintenance régulière
from apps.data_warehouse.services import DataWarehouseService

service = DataWarehouseService()

for table in DataWarehouseTable.objects.all():
    if table.row_count > 1000000:
        service.analyze_table(table)
        if table.deleted_rows > table.row_count * 0.2:
            service.optimize_table(table)
```

### 4. Stratégies d'Agrégation

```python
# Création d'agrégations pour les requêtes fréquentes
AggregationTable.objects.create(
    name="ventes_quotidien_agg",
    base_table=ventes_fait,
    granularity="daily",
    group_by_columns=["date_id", "produit_id"],
    aggregated_columns=[
        "SUM(montant) as total_ventes", 
        "COUNT(*) as nb_transactions"
    ],
    refresh_frequency="hourly"
)
```

---

## Dépannage

### Problèmes Courants et Solutions

| Problème | Solution |
|----------|----------|
| Requêtes lentes | Vérifier les index, créer des agrégations, analyser les tables |
| Échec de rafraîchissement | Vérifier les données sources, consulter les logs, réessayer avec des lots plus petits |
| Problèmes de partitionnement | Valider les limites des partitions, vérifier la fonction de partition |
| Erreurs mémoire | Utiliser le traitement par lots, augmenter `batch_size`, optimiser les requêtes |

### Débogage

```python
# Activation des logs de débogage
import logging
logging.getLogger('apps.data_warehouse').setLevel(logging.DEBUG)

# Consultation des logs récents
from apps.data_warehouse.models import DataWarehouseLog

erreurs = DataWarehouseLog.objects.filter(level='error')[:10]
for erreur in erreurs:
    print(f"{erreur.created_at}: {erreur.message}")

# Surveillance des métriques
from apps.data_warehouse.models import DataWarehouseMetric

metriques = DataWarehouseMetric.objects.filter(
    table__name='ventes_fait',
    timestamp__gte=timezone.now() - timedelta(hours=24)
).order_by('-timestamp')
```

---

## Historique des Versions

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0.0 | 2026-03-05 | Version initiale avec modèles principaux, schémas en étoile et API |
```

Cette documentation fournit un guide complet du module Data Warehouse, incluant :
- Des descriptions détaillées des modèles avec exemples
- Les patterns de conception des schémas en étoile
- Les endpoints API et leur utilisation
- Les bonnes pratiques de nommage et d'optimisation
- Les stratégies de tuning des performances
- Un guide de dépannage