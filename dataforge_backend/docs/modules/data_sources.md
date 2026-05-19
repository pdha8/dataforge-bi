## **`dataforge_backend/docs/modules/data_sources.md`**

```markdown
# 🗄️ DataForge Data Sources - Documentation Technique

## Table des matières
1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Modèles de Données](#modèles-de-données)
4. [Types de Sources Supportées](#types-de-sources-supportées)
5. [API REST](#api-rest)
6. [Services](#services)
7. [Gestion des Fichiers](#gestion-des-fichiers)
8. [Power Query](#power-query)
9. [Schémas en Étoile](#schémas-en-étoile)
10. [Monitoring et Métriques](#monitoring-et-métriques)
11. [Bonnes Pratiques](#bonnes-pratiques)
12. [Exemples d'Utilisation](#exemples-dutilisation)

---

## Introduction

Le module **Data Sources** de DataForge BI est responsable de la gestion de toutes les sources de données de la plateforme. Il supporte plus de **25 types de sources** différents, allant des bases de données relationnelles aux APIs, en passant par les fichiers et le cloud storage.

### 🎯 Objectifs
- 🔌 **Connectivité universelle** - Support de 25+ types de sources
- 📁 **Gestion de fichiers** - Upload et traitement de fichiers
- 🔄 **ETL intégré** - Transformations Power Query (langage M)
- 📊 **Star Schema** - Modélisation data warehouse
- 📈 **Monitoring** - Métriques de performance et logs
- 🔒 **Sécurité** - Gestion des identifiants et accès

---

## Architecture

```
apps/data_sources/
├── __init__.py              # Configuration du module
├── admin.py                 # Interface d'administration
├── apps.py                  # Configuration Django
├── choices.py               # Export des constantes
├── constants.py             # 25+ types de sources
├── enums.py                 # Enums Python
├── filters.py               # Filtres API
├── managers.py              # Gestionnaires personnalisés
├── migrations/              # Migrations Django
├── models.py                # Modèles de données (11 modèles)
├── serializers.py           # Sérialiseurs API
├── services.py              # Services métier
├── signals.py               # Signaux Django
├── urls.py                  # Routes API
├── validators.py            # Validateurs
└── views.py                 # Vues API REST
```

---

## Modèles de Données

### 📌 **DataSource - Source de données principale**

Modèle central gérant toutes les configurations de connexion.

```python
from apps.data_sources.models import DataSource

# Créer une source PostgreSQL
source = DataSource.objects.create(
    name="Base de données Production",
    description="Base de données principale de l'application",
    source_type="postgresql",
    host="db.production.com",
    port=5432,
    database_name="app_db",
    username="app_user",
    password="secure_password",
    status="active",
    sync_frequency="hourly"
)
```

#### Champs Principaux

| Champ | Type | Description |
|-------|------|-------------|
| `name` | CharField | Nom de la source |
| `source_type` | ChoiceField | Type de source (25+ options) |
| `status` | ChoiceField | Statut (draft, active, error, etc.) |
| `connection_string` | TextField | Chaîne de connexion complète |
| `host` | CharField | Hôte du serveur |
| `port` | IntegerField | Port de connexion |
| `database_name` | CharField | Nom de la base de données |
| `sync_frequency` | ChoiceField | Fréquence de synchronisation |
| `data_quality_score` | IntegerField | Score de qualité (0-100) |
| `total_queries` | BigIntegerField | Nombre total de requêtes |

#### Propriétés Utiles

```python
# Vérifier si la source est connectée
source.is_connected  # True si status='active'

# Taux de succès des requêtes
source.success_rate  # 95.5

# Taille des données en MB
source.data_size_mb  # 125.3

# État de santé
source.health_status  # 'good', 'fair', 'warning', 'critical'

# Vérifier si synchronisation nécessaire
source.needs_sync  # True si dépassé
```

#### Méthodes

```python
# Tester la connexion
result = source.test_connection()
# {'success': True, 'message': 'Connexion réussie', 'latency_ms': 45}

# Exécuter une requête
result = source.execute_query("SELECT * FROM users LIMIT 10")
# {'success': True, 'data': [...], 'row_count': 10}

# Synchroniser les tables
result = source.sync_tables()
# {'success': True, 'tables_created': 5, 'tables_updated': 12}

# Enregistrer une erreur
source.log_error("Timeout de connexion")

# Calculer le score de qualité
source.calculate_quality_score()  # 85
```

### 📌 **DataTable - Tables découvertes**

```python
from apps.data_sources.models import DataTable

# Tables automatiquement découvertes lors de sync_tables()
tables = source.tables.all()
for table in tables:
    print(table.full_name)          # "public.users"
    print(table.column_count)       # 15
    print(table.columns)            # Liste des colonnes
    print(table.primary_key)        # ['id']
```

### 📌 **DataQuery - Requêtes enregistrées**

```python
from apps.data_sources.models import DataQuery

# Créer une requête enregistrée
query = DataQuery.objects.create(
    data_source=source,
    name="Utilisateurs actifs",
    description="Liste des utilisateurs actifs du dernier mois",
    query_type="sql",
    query_text="SELECT * FROM users WHERE is_active = true AND last_login > NOW() - INTERVAL '30 days'",
    is_favorite=True
)

# Exécuter la requête
result = query.execute({'limit': 100})
# {'success': True, 'data': [...], 'from_cache': False}

# Vider le cache
query.clear_cache()
```

### 📌 **DataSourceFile - Fichiers uploadés**

```python
from apps.data_sources.models import DataSourceFile

# Upload de fichier
file = DataSourceFile.objects.create(
    data_source=source,
    file=uploaded_file,
    original_name="ventes_2024.xlsx",
    file_type="excel",
    sheet_name="Ventes"
)

# Traiter le fichier
file.process()  # Analyse automatique
print(file.row_count)      # 15000
print(file.preview_data)   # 10 premières lignes
print(file.schema)         # Structure détectée
```

### 📌 **PowerQuery - Transformations M**

```python
from apps.data_sources.models import PowerQuery, QueryStep

# Créer un Power Query
pq = PowerQuery.objects.create(
    data_source=source,
    name="Nettoyage ventes",
    description="Nettoyage et agrégation des données de ventes",
    is_enabled=True
)

# Ajouter des étapes
QueryStep.objects.create(
    power_query=pq,
    step_order=1,
    step_type="filter",
    step_config={"column": "montant", "operator": ">", "value": 0}
)

QueryStep.objects.create(
    power_query=pq,
    step_order=2,
    step_type="group",
    step_config={"by": ["categorie"], "aggregations": [{"column": "montant", "func": "sum"}]}
)

# Exécuter
result = pq.execute()
```

### 📌 **StarSchema - Schéma en étoile**

```python
from apps.data_sources.models import StarSchema

# Créer un schéma en étoile
schema = StarSchema.objects.create(
    name="Analyse des ventes",
    description="Schéma en étoile pour l'analyse des ventes",
    fact_table=fact_table,
    measures=[
        {"column": "montant", "aggregation": "SUM", "alias": "total_ventes"},
        {"column": "quantite", "aggregation": "SUM", "alias": "total_quantite"}
    ],
    dimension_columns={
        "dim_date": ["annee", "mois", "jour"],
        "dim_produit": ["nom", "categorie"],
        "dim_client": ["nom", "ville"]
    }
)

# Générer la requête SQL
sql = schema.generate_query()
print(sql)
# SELECT dim_date.annee, dim_date.mois, dim_date.jour, 
#        dim_produit.nom, dim_produit.categorie,
#        dim_client.nom, dim_client.ville,
#        SUM(fait.montant) AS total_ventes,
#        SUM(fait.quantite) AS total_quantite
# FROM ventes_fait
# LEFT JOIN dim_date ON fait.date_id = dim_date.id
# LEFT JOIN dim_produit ON fait.produit_id = dim_produit.id
# LEFT JOIN dim_client ON fait.client_id = dim_client.id
# GROUP BY dim_date.annee, dim_date.mois, dim_date.jour, dim_produit.nom, ...
```

### 📌 **DataSourceLog - Journal d'activité**

```python
from apps.data_sources.models import DataSourceLog

# Logs automatiquement créés
logs = source.logs.filter(level='error')
for log in logs:
    print(log.message)          # Message d'erreur
    print(log.execution_time_ms) # Temps d'exécution
```

### 📌 **DataSourceMetric - Métriques de performance**

```python
from apps.data_sources.models import DataSourceMetric

# Métriques automatiquement enregistrées
metrics = source.metrics.filter(query_time_ms__gt=1000)  # Requêtes lentes
for metric in metrics:
    print(f"Requête: {metric.query_time_ms}ms, {metric.rows_returned} lignes")
```

---

## Types de Sources Supportées

### 📁 **Fichiers**
| Type | Extension | Description |
|------|-----------|-------------|
| Excel | .xlsx, .xls | Fichiers Excel avec feuilles multiples |
| CSV | .csv | Fichiers CSV avec délimiteur configurable |
| JSON | .json | Fichiers JSON structurés |
| XML | .xml | Fichiers XML |
| Parquet | .parquet | Format columnar optimisé |
| Avro | .avro | Format de données binaires |
| TXT | .txt | Fichiers texte avec délimiteur |

### 🗄️ **Bases de données relationnelles**
| Type | Bibliothèque | Port par défaut |
|------|--------------|----------------|
| PostgreSQL | psycopg2 | 5432 |
| MySQL | mysqlclient | 3306 |
| SQL Server | pyodbc | 1433 |
| Oracle | cx_Oracle | 1521 |
| SQLite | sqlite3 | - |
| IBM Db2 | ibm_db | 50000 |

### 🍃 **NoSQL**
| Type | Bibliothèque | Port par défaut |
|------|--------------|----------------|
| MongoDB | pymongo | 27017 |
| Redis | redis | 6379 |
| Elasticsearch | elasticsearch | 9200 |
| Cassandra | cassandra-driver | 9042 |
| DynamoDB | boto3 | 443 |

### ☁️ **Cloud Data Warehouse**
| Type | Bibliothèque | Description |
|------|--------------|-------------|
| BigQuery | google-cloud-bigquery | Google BigQuery |
| Snowflake | snowflake-connector-python | Snowflake |
| Redshift | psycopg2 | Amazon Redshift |
| Azure SQL | pyodbc | Azure SQL Database |
| Databricks | databricks-sql-connector | Databricks |

### 🌐 **APIs**
| Type | Description |
|------|-------------|
| REST | APIs RESTful standard |
| GraphQL | APIs GraphQL |
| SOAP | APIs SOAP/WSDL |
| OData | OData feeds |

### 📦 **Cloud Storage**
| Type | Bibliothèque | Description |
|------|--------------|-------------|
| Amazon S3 | boto3 | Amazon Simple Storage Service |
| Azure Blob | azure-storage-blob | Azure Blob Storage |
| Google Cloud Storage | google-cloud-storage | GCS |
| Google Drive | google-drive-api | Google Drive |
| SharePoint | office365-rest-python-client | SharePoint |
| OneDrive | msgraph-sdk | OneDrive |

### 📡 **Streaming**
| Type | Bibliothèque | Description |
|------|--------------|-------------|
| Apache Kafka | kafka-python | Streaming Kafka |
| Amazon Kinesis | boto3 | Streaming Kinesis |

---

## API REST

### 📌 **Endpoints**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/data-sources/sources/` | Liste des sources |
| POST | `/api/data-sources/sources/` | Créer une source |
| GET | `/api/data-sources/sources/{id}/` | Détail source |
| PUT | `/api/data-sources/sources/{id}/` | Mettre à jour |
| DELETE | `/api/data-sources/sources/{id}/` | Supprimer |
| POST | `/api/data-sources/sources/{id}/test_connection/` | Tester connexion |
| POST | `/api/data-sources/sources/{id}/execute_query/` | Exécuter requête |
| POST | `/api/data-sources/sources/{id}/sync_tables/` | Synchroniser tables |
| GET | `/api/data-sources/sources/{id}/tables/` | Liste des tables |
| GET | `/api/data-sources/sources/{id}/queries/` | Liste des requêtes |
| GET | `/api/data-sources/sources/{id}/logs/` | Liste des logs |
| GET | `/api/data-sources/sources/{id}/metrics/` | Liste des métriques |
| GET | `/api/data-sources/sources/stats/` | Statistiques globales |

### 📌 **Exemples d'utilisation**

```bash
# Tester une connexion
curl -X POST http://localhost:8000/api/data-sources/sources/1/test_connection/

# Exécuter une requête
curl -X POST http://localhost:8000/api/data-sources/sources/1/execute_query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users LIMIT 10"}'

# Créer une source
curl -X POST http://localhost:8000/api/data-sources/sources/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production DB",
    "source_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "app_db",
    "username": "user",
    "password": "pass"
  }'

# Uploader un fichier
curl -X POST http://localhost:8000/api/data-sources/files/ \
  -F "data_source=1" \
  -F "file=@data.csv"
```

---

## Services

### 📌 **DataSourceService**

Service principal pour interagir avec les sources de données.

```python
from apps.data_sources.services import DataSourceService

source = DataSource.objects.get(id=1)
service = DataSourceService(source)

# Tester la connexion
result = service.test_connection()

# Exécuter une requête
result = service.execute_query("SELECT * FROM users")

# Synchroniser les tables
result = service.sync_tables()
```

### 📌 **QueryService**

Service pour les requêtes enregistrées avec cache.

```python
from apps.data_sources.services import QueryService

query = DataQuery.objects.get(id=1)
service = QueryService(query)

# Exécuter avec cache
result = service.execute({'limit': 100})

# Vider le cache
service.clear_cache()
```

---

## Gestion des Fichiers

### 📌 **Upload de fichiers**

```python
# Créer un fichier
file = DataSourceFile.objects.create(
    data_source=source,
    file=uploaded_file,
    original_name="data.csv",
    file_type="csv",
    encoding="utf-8",
    delimiter=","
)

# Traitement automatique
file.process()
print(file.process_status)  # 'completed'
print(file.row_count)       # 10000
print(file.preview_data)    # Aperçu
```

### 📌 **Formats supportés**

| Format | Méthodes de lecture | Options |
|--------|---------------------|---------|
| CSV | `pd.read_csv()` | encoding, delimiter, header |
| Excel | `pd.read_excel()` | sheet_name, header |
| JSON | `pd.read_json()` | orient, lines |
| Parquet | `pd.read_parquet()` | engine |

---

## Power Query

### 📌 **Étapes de transformation**

| Étape | Description | Configuration |
|-------|-------------|---------------|
| `source` | Source de données | data_source, table |
| `filter` | Filtrer les lignes | column, operator, value |
| `sort` | Trier | column, order |
| `group` | Grouper par | by, aggregations |
| `aggregate` | Agréger | column, function |
| `merge` | Fusionner | left, right, on |
| `append` | Ajouter | tables |
| `pivot` | Pivoter | rows, columns, values |
| `unpivot` | Dépivoter | columns |
| `rename` | Renommer | mapping |
| `remove` | Supprimer | columns |
| `split` | Diviser | column, delimiter |
| `replace` | Remplacer | column, old, new |
| `transform` | Transformer | column, function |
| `add_column` | Ajouter colonne | name, expression |
| `change_type` | Changer type | column, new_type |
| `custom` | Code M personnalisé | m_code |

### 📌 **Exemple complet**

```python
# Créer un Power Query
pq = PowerQuery.objects.create(
    data_source=source,
    name="Nettoyage données"
)

# Étape 1: Filtrer
QueryStep.objects.create(
    power_query=pq,
    step_order=1,
    step_type="filter",
    step_config={"column": "age", "operator": ">=", "value": 18}
)

# Étape 2: Grouper
QueryStep.objects.create(
    power_query=pq,
    step_order=2,
    step_type="group",
    step_config={
        "by": ["region"],
        "aggregations": [
            {"column": "montant", "func": "sum", "alias": "total"},
            {"column": "montant", "func": "avg", "alias": "moyenne"}
        ]
    }
)

# Étape 3: Trier
QueryStep.objects.create(
    power_query=pq,
    step_order=3,
    step_type="sort",
    step_config={"column": "total", "order": "desc"}
)

# Exécuter
result = pq.execute()
```

---

## Schémas en Étoile

### 📌 **Concepts**

Un schéma en étoile est une modélisation de données pour l'analyse BI, composée de :

- **Table des faits** : Contient les mesures (chiffres à analyser)
- **Tables de dimensions** : Contiennent les attributs descriptifs

### 📌 **Exemple de création**

```python
# Tables
fact_sales = DataTable.objects.get(name="ventes")
dim_date = DataTable.objects.get(name="dim_date")
dim_product = DataTable.objects.get(name="dim_produit")
dim_customer = DataTable.objects.get(name="dim_client")

# Créer le schéma
schema = StarSchema.objects.create(
    name="Analyse des ventes",
    description="Schéma en étoile pour l'analyse des ventes",
    fact_table=fact_sales,
    measures=[
        {"column": "montant", "aggregation": "SUM", "alias": "total_ventes"},
        {"column": "quantite", "aggregation": "SUM", "alias": "total_quantite"},
        {"column": "montant", "aggregation": "AVG", "alias": "montant_moyen"}
    ],
    dimension_columns={
        "dim_date": ["annee", "mois", "jour", "trimestre"],
        "dim_produit": ["nom", "categorie", "prix_unitaire"],
        "dim_client": ["nom", "ville", "segment"]
    }
)

# Ajouter les dimensions
schema.dimension_tables.add(dim_date, dim_product, dim_customer)

# Générer la requête
sql = schema.generate_query()

# Exécuter
result = schema.execute()
```

---

## Monitoring et Métriques

### 📌 **Métriques automatiques**

| Métrique | Description |
|----------|-------------|
| `total_queries` | Nombre total de requêtes |
| `successful_queries` | Requêtes réussies |
| `failed_queries` | Requêtes échouées |
| `avg_query_time_ms` | Temps moyen de requête |
| `last_query_time` | Date dernière requête |
| `error_count` | Nombre d'erreurs |
| `consecutive_failures` | Échecs consécutifs |
| `data_quality_score` | Score de qualité (0-100) |

### 📌 **Filtres de logs**

```python
# Récupérer les erreurs des dernières 24h
errors = DataSourceLog.objects.filter(
    data_source=source,
    level='error',
    created_at__gte=timezone.now() - timedelta(hours=24)
)

# Récupérer les requêtes lentes
slow_queries = DataSourceMetric.objects.filter(
    data_source=source,
    query_time_ms__gt=5000
)
```

---

## Bonnes Pratiques

### ✅ **À FAIRE**

1. **Toujours tester la connexion avant utilisation**
```python
if source.test_connection()['success']:
    result = source.execute_query(query)
```

2. **Utiliser les requêtes enregistrées pour les requêtes fréquentes**
```python
query = DataQuery.objects.create(
    data_source=source,
    name="Ventes journalières",
    query_text=sql,
    is_cached=True,
    cache_ttl=3600
)
```

3. **Journaliser les erreurs**
```python
try:
    result = source.execute_query(query)
except Exception as e:
    source.log_error(str(e))
```

4. **Surveiller la qualité des données**
```python
if source.data_quality_score < 70:
    # Alerter l'équipe
    send_alert(f"Source {source.name} - Qualité faible")
```

### ❌ **À ÉVITER**

1. **Ne pas exposer les mots de passe en clair**
2. **Ne pas exécuter de requêtes non validées**
3. **Ne pas ignorer les erreurs de connexion**
4. **Ne pas surcharger avec des requêtes trop fréquentes**

---

## Exemples d'Utilisation

### 📌 **Connexion à PostgreSQL**

```python
# Créer la source
source = DataSource.objects.create(
    name="PostgreSQL Prod",
    source_type="postgresql",
    host="db.production.com",
    port=5432,
    database_name="app_db",
    username="readonly_user",
    password="secure_pass",
    sync_frequency="daily"
)

# Tester
source.test_connection()

# Exécuter une requête
result = source.execute_query("""
    SELECT DATE(created_at) as date, COUNT(*) as count
    FROM users
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY date
""")

# Afficher les résultats
for row in result['data']:
    print(f"{row['date']}: {row['count']} utilisateurs")
```

### 📌 **Import de fichier Excel**

```python
# Upload du fichier
file = DataSourceFile.objects.create(
    data_source=source,
    file=request.FILES['file'],
    original_name="ventes_2024.xlsx",
    file_type="excel",
    sheet_name="Ventes 2024"
)

# Traitement
file.process()

# Analyser les données
print(f"Lignes: {file.row_count}")
print(f"Colonnes: {file.column_count}")
print(f"Aperçu: {file.preview_data}")

# Créer une requête Power Query pour nettoyer
pq = PowerQuery.objects.create(
    data_source=source,
    name="Nettoyage ventes"
)

# Étapes de nettoyage
QueryStep.objects.create(
    power_query=pq,
    step_order=1,
    step_type="filter",
    step_config={"column": "montant", "operator": ">", "value": 0}
)

QueryStep.objects.create(
    power_query=pq,
    step_order=2,
    step_type="remove",
    step_config={"columns": ["commentaire", "notes"]}
)

QueryStep.objects.create(
    power_query=pq,
    step_order=3,
    step_type="change_type",
    step_config={"date_vente": "datetime", "montant": "float"}
)

# Exécuter
cleaned_data = pq.execute()
```

### 📌 **Dashboard avec schéma en étoile**

```python
# Créer le schéma en étoile
schema = StarSchema.objects.create(
    name="Tableau de bord ventes",
    fact_table=fact_sales,
    measures=[
        {"column": "montant", "aggregation": "SUM", "alias": "CA"},
        {"column": "quantite", "aggregation": "SUM", "alias": "Qte"},
        {"column": "montant", "aggregation": "AVG", "alias": "Panier moyen"}
    ],
    dimension_columns={
        "dim_date": ["annee", "mois"],
        "dim_produit": ["categorie"],
        "dim_client": ["segment"]
    }
)

# Générer les requêtes pour différents KPIs
kpis = {
    "ca_total": "SELECT SUM(CA) FROM ({})".format(schema.generate_query()),
    "ca_par_mois": "SELECT mois, SUM(CA) FROM ({}) GROUP BY mois".format(schema.generate_query()),
    "ca_par_categorie": "SELECT categorie, SUM(CA) FROM ({}) GROUP BY categorie".format(schema.generate_query())
}

# Exécuter et afficher
for name, query in kpis.items():
    result = source.execute_query(query)
    print(f"{name}: {result['data']}")
```

---

## Dépannage

### 🐛 **Problèmes courants**

| Problème | Cause | Solution |
|----------|-------|----------|
| Échec connexion | Identifiants incorrects | Vérifier username/password |
| Timeout | Latence réseau | Augmenter timeout_seconds |
| SQLAlchemy non installé | Bibliothèque manquante | `uv add sqlalchemy` |
| Fichier non trouvé | Chemin incorrect | Vérifier file_path |
| Permission refusée | Droits insuffisants | Vérifier les permissions |

---

## Conclusion

Le module Data Sources de DataForge offre une solution complète et professionnelle pour la gestion des sources de données BI avec :

- 🔌 **25+ types de sources** supportés
- 📁 **Gestion de fichiers** avancée
- 🔄 **Power Query** intégré
- 📊 **Star Schema** pour le data warehouse
- 📈 **Monitoring** complet
- 🔒 **Sécurité** renforcée

---

**Version:** 1.0.0  
**Dernière mise à jour:** 24 Février 2026  
**Mainteneur:** DataForge
```