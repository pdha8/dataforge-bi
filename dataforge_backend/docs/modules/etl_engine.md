## **`dataforge_backend/docs/modules/etl_engine.md`**

```markdown
# 🔄 DataForge ETL Engine - Documentation Technique

## Table des matières
1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Modèles de Données](#modèles-de-données)
4. [Types de Pipelines](#types-de-pipelines)
5. [Transformations](#transformations)
6. [API REST](#api-rest)
7. [Services](#services)
8. [Planification](#planification)
9. [Monitoring et Métriques](#monitoring-et-métriques)
10. [Notifications](#notifications)
11. [Bonnes Pratiques](#bonnes-pratiques)
12. [Exemples d'Utilisation](#exemples-dutilisation)

---

## Introduction

Le module **ETL Engine** de DataForge BI est le cœur du traitement des données. Il orchestre l'extraction, la transformation et le chargement des données entre différentes sources et destinations.

### 🎯 Objectifs
- 🔄 **Orchestration ETL/ELT** - Gestion complète des pipelines de données
- 🔧 **Transformations avancées** - 18+ types de transformations
- ⏰ **Planification flexible** - CRON, fréquences prédéfinies, dépendances
- 📊 **Monitoring détaillé** - Métriques de performance, logs d'exécution
- 🔔 **Notifications** - Alertes en temps réel sur les exécutions
- 🚨 **Gestion des erreurs** - Stratégies robustes (fail, skip, retry, notify)

---

## Architecture

```
apps/etl_engine/
├── __init__.py              # Configuration du module
├── admin.py                 # Interface d'administration
├── apps.py                  # Configuration Django
├── constants.py             # Constantes (types de pipelines, statuts, etc.)
├── enums.py                 # Enums Python
├── filters.py               # Filtres API
├── managers.py              # Gestionnaires personnalisés
├── migrations/              # Migrations Django
├── models.py                # Modèles de données (6 modèles)
├── serializers.py           # Sérialiseurs API
├── services.py              # Services métier (exécution pipelines)
├── signals.py               # Signaux Django
├── urls.py                  # Routes API
├── validators.py            # Validateurs (CRON, Python, SQL)
└── views.py                 # Vues API REST
```

---

## Modèles de Données

### 📌 **ETLPipeline - Pipeline ETL principal**

Modèle central orchestrant l'ensemble du processus ETL.

```python
from apps.etl_engine.models import ETLPipeline

# Créer un pipeline
pipeline = ETLPipeline.objects.create(
    name="Analyse des ventes",
    description="Pipeline quotidien d'analyse des ventes",
    pipeline_type="etl",
    status="active",
    source=postgres_source,
    target=warehouse_target,
    schedule_enabled=True,
    schedule_frequency="daily",
    batch_size=10000,
    error_strategy="skip"
)
```

#### Champs Principaux

| Champ | Type | Description |
|-------|------|-------------|
| `name` | CharField | Nom du pipeline |
| `pipeline_type` | ChoiceField | Type (etl, elt, extract, load, replication, migration, aggregation, cleaning) |
| `status` | ChoiceField | Statut (draft, active, paused, error, archived, deprecated) |
| `source` | ForeignKey | Source de données (DataSource) |
| `target` | ForeignKey | Cible de données (DataSource) |
| `schedule_enabled` | BooleanField | Planification activée |
| `schedule_frequency` | ChoiceField | Fréquence (realtime, hourly, daily, weekly, monthly) |
| `schedule_cron` | CharField | Expression CRON personnalisée |
| `batch_size` | IntegerField | Taille de lot (100-100000) |
| `timeout_seconds` | IntegerField | Timeout (10-86400 secondes) |
| `error_strategy` | ChoiceField | Stratégie d'erreur (fail, skip, default, retry, notify, continue) |
| `retry_policy` | JSONField | Politique de réessai |

#### Propriétés Utiles

```python
# Taux de succès
pipeline.success_rate  # 95.5

# État de santé
pipeline.health_status  # 'good', 'fair', 'warning', 'critical'

# Vérifier si une exécution est nécessaire
pipeline.needs_execution  # True/False

# Calculer la prochaine exécution
pipeline.calculate_next_execution()
```

#### Méthodes

```python
# Mettre à jour les métriques après exécution
pipeline.update_metrics(duration_seconds=120, rows_processed=50000, success=True)

# Enregistrer une erreur
pipeline.log_error("Erreur de connexion à la source", step_name="extract")

# Calculer le score de qualité
pipeline.calculate_quality_score()  # 85
```

### 📌 **Transformation - Étape de transformation**

Transformation individuelle appliquée aux données.

```python
from apps.etl_engine.models import Transformation

transformation = Transformation.objects.create(
    pipeline=pipeline,
    order=1,
    name="Filtrer ventes",
    description="Garder uniquement les ventes > 100€",
    transformation_type="filter",
    config={
        "column": "montant",
        "operator": "gt",
        "value": 100
    },
    is_critical=True
)
```

#### Types de transformations

| Type | Description | Configuration |
|------|-------------|---------------|
| `filter` | Filtrer les lignes | `{"column": "montant", "operator": "gt", "value": 100}` |
| `select` | Sélectionner des colonnes | `{"columns": ["nom", "prix"]}` |
| `rename` | Renommer des colonnes | `{"mapping": {"old": "new"}}` |
| `cast` | Changer le type | `{"types": {"age": "int", "date": "datetime"}}` |
| `aggregate` | Agréger des données | `{"group_by": ["categorie"], "aggregations": {"montant": "sum"}}` |
| `join` | Fusionner des tables | `{"left": "table1", "right": "table2", "on": "id"}` |
| `custom_python` | Code Python personnalisé | `{"code": "df['total'] = df['prix'] * df['quantite']"}` |
| `custom_sql` | SQL personnalisé | `{"query": "SELECT * FROM table"}` |
| `deduplicate` | Supprimer les doublons | `{"subset": ["id"], "keep": "first"}` |
| `fillna` | Remplir les valeurs nulles | `{"value": 0, "columns": ["montant"]}` |
| `dropna` | Supprimer les valeurs nulles | `{"subset": ["id"], "how": "any"}` |
| `sort` | Trier | `{"by": ["date"], "ascending": True}` |

### 📌 **ExecutionLog - Journal d'exécution**

Trace complète de chaque exécution de pipeline.

```python
from apps.etl_engine.models import ExecutionLog

# Journal automatiquement créé lors de l'exécution
log = ExecutionLog.objects.filter(pipeline=pipeline).first()
print(log.status)           # 'completed'
print(log.duration_seconds) # 125.5
print(log.rows_read)        # 100000
print(log.rows_written)     # 98500
print(log.rows_errors)      # 1500
```

### 📌 **SourceSchema - Schéma source**

Définition de la source pour l'extraction.

```python
from apps.etl_engine.models import SourceSchema

source_schema = SourceSchema.objects.create(
    pipeline=pipeline,
    query="SELECT * FROM ventes WHERE date > '2024-01-01'",
    filters=[{"column": "statut", "operator": "eq", "value": "valide"}],
    selected_columns=["id", "montant", "date"],
    incremental_column="date",
    last_value="2024-01-01"
)
```

### 📌 **TargetSchema - Schéma cible**

Définition de la destination pour le chargement.

```python
from apps.etl_engine.models import TargetSchema

target_schema = TargetSchema.objects.create(
    pipeline=pipeline,
    table_name="ventes_analyse",
    columns=[
        {"name": "id", "type": "INTEGER", "nullable": False},
        {"name": "montant", "type": "DECIMAL(10,2)"},
        {"name": "date", "type": "DATE"}
    ],
    primary_key=["id"],
    insert_strategy="upsert",
    upsert_keys=["id"],
    is_partitioned=True,
    partition_column="date",
    partition_type="range"
)
```

#### Stratégies d'insertion

| Stratégie | Description |
|-----------|-------------|
| `append` | Ajouter les données (INSERT) |
| `upsert` | Mettre à jour ou insérer (INSERT ... ON CONFLICT) |
| `merge` | Fusionner avec les données existantes |
| `replace` | Remplacer complètement la table |
| `truncate_insert` | Vider puis insérer |

### 📌 **PipelineNotification - Notifications**

Configuration des notifications par pipeline.

```python
from apps.etl_engine.models import PipelineNotification

notification = PipelineNotification.objects.create(
    pipeline=pipeline,
    channel="slack",
    recipient="#etl-alerts",
    config={"webhook_url": "https://hooks.slack.com/..."},
    send_on_start=True,
    send_on_success=True,
    send_on_failure=True
)
```

---

## Types de Pipelines

| Type | Description | Cas d'usage |
|------|-------------|-------------|
| **ETL** | Extract-Transform-Load | Pipeline standard avec transformation |
| **ELT** | Extract-Load-Transform | Chargement rapide, transformation dans la cible |
| **Extract** | Extraction uniquement | Export de données brutes |
| **Load** | Chargement uniquement | Import de données pré-transformées |
| **Replication** | Réplication | Synchronisation entre bases |
| **Migration** | Migration | Transfert de données entre systèmes |
| **Aggregation** | Agrégation | Calculs de métriques et KPI |
| **Cleaning** | Nettoyage | Nettoyage de données (duplicates, nulls) |

---

## Transformations

### 📌 **Exemples de transformations**

#### 1. Filtrage des données
```json
{
    "type": "filter",
    "config": {
        "column": "montant",
        "operator": "gt",
        "value": 100
    }
}
```

#### 2. Agrégation par catégorie
```json
{
    "type": "aggregate",
    "config": {
        "group_by": ["categorie", "region"],
        "aggregations": {
            "total_ventes": "sum",
            "nb_ventes": "count",
            "moyenne": "avg"
        }
    }
}
```

#### 3. Code Python personnalisé
```json
{
    "type": "custom_python",
    "custom_code": "df['score'] = df['ventes'] / df['objectif'] * 100"
}
```

#### 4. Jointure entre tables
```json
{
    "type": "join",
    "config": {
        "left": "ventes",
        "right": "clients",
        "on": "client_id",
        "how": "left"
    }
}
```

---

## API REST

### 📌 **Endpoints**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/etl/pipelines/` | Liste des pipelines |
| POST | `/api/etl/pipelines/` | Créer un pipeline |
| GET | `/api/etl/pipelines/{id}/` | Détail d'un pipeline |
| PUT | `/api/etl/pipelines/{id}/` | Mettre à jour |
| DELETE | `/api/etl/pipelines/{id}/` | Supprimer |
| POST | `/api/etl/pipelines/{id}/execute/` | Exécuter le pipeline |
| GET | `/api/etl/pipelines/{id}/executions/` | Historique des exécutions |
| GET | `/api/etl/pipelines/{id}/transformations/` | Liste des transformations |
| GET | `/api/etl/transformations/` | Liste des transformations |
| POST | `/api/etl/transformations/` | Créer une transformation |
| GET | `/api/etl/executions/` | Liste des exécutions |
| GET | `/api/etl/executions/stats/` | Statistiques des exécutions |
| GET | `/api/etl/target-schemas/` | Schémas cibles |
| GET | `/api/etl/source-schemas/` | Schémas sources |
| GET | `/api/etl/notifications/` | Notifications |

### 📌 **Exemples d'utilisation**

```bash
# Créer un pipeline
curl -X POST http://localhost:8000/api/etl/pipelines/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Analyse ventes",
    "pipeline_type": "etl",
    "source": 1,
    "target": 2,
    "schedule_enabled": true,
    "schedule_frequency": "daily"
  }'

# Exécuter un pipeline
curl -X POST http://localhost:8000/api/etl/pipelines/1/execute/

# Ajouter une transformation
curl -X POST http://localhost:8000/api/etl/transformations/ \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": 1,
    "order": 1,
    "name": "Filtrer ventes",
    "transformation_type": "filter",
    "config": {
      "column": "montant",
      "operator": "gt",
      "value": 0
    }
  }'

# Voir les exécutions
curl http://localhost:8000/api/etl/executions/?pipeline=1
```

---

## Services

### 📌 **ETLPipelineService**

Service principal d'exécution des pipelines.

```python
from apps.etl_engine.services import ETLPipelineService

pipeline = ETLPipeline.objects.get(id=1)
service = ETLPipelineService(pipeline)

# Exécuter le pipeline
result = service.execute(
    params={"date_debut": "2024-01-01"},
    triggered_by="api",
    user=request.user
)

print(result)
# {
#     'success': True,
#     'execution_id': 'abc-123',
#     'rows_read': 100000,
#     'rows_written': 98500,
#     'duration_seconds': 125.5
# }
```

### 📌 **ETLOrchestrator**

Orchestrateur pour les pipelines avec dépendances.

```python
from apps.etl_engine.services import ETLOrchestrator

orchestrator = ETLOrchestrator()

# Exécuter un pipeline avec ses dépendances
result = orchestrator.execute_pipeline(1)

# Exécuter plusieurs pipelines en parallèle
results = orchestrator.execute_pipelines([1, 2, 3, 4])
```

---

## Planification

### 📌 **Fréquences supportées**

| Fréquence | Description |
|-----------|-------------|
| `realtime` | Temps réel (10 secondes) |
| `every_5m` | Toutes les 5 minutes |
| `every_15m` | Toutes les 15 minutes |
| `every_30m` | Toutes les 30 minutes |
| `hourly` | Horaire |
| `every_6h` | Toutes les 6 heures |
| `daily` | Quotidien |
| `weekly` | Hebdomadaire |
| `monthly` | Mensuel |
| `manual` | Manuel (pas de planification) |

### 📌 **CRON personnalisé**

```python
# Exemple: Tous les jours à 2h du matin
pipeline.schedule_cron = "0 2 * * *"

# Exemple: Toutes les heures, de 9h à 18h
pipeline.schedule_cron = "0 9-18 * * *"

# Exemple: Tous les lundis à 8h
pipeline.schedule_cron = "0 8 * * 1"
```

### 📌 **Dépendances entre pipelines**

```python
# Pipeline B dépend de pipeline A
pipeline_b.dependencies.add(pipeline_a)

# Pipeline C dépend de A et B
pipeline_c.dependencies.add(pipeline_a, pipeline_b)
```

---

## Monitoring et Métriques

### 📌 **Métriques automatiques**

| Métrique | Description |
|----------|-------------|
| `execution_count` | Nombre total d'exécutions |
| `success_count` | Nombre de succès |
| `failure_count` | Nombre d'échecs |
| `success_rate` | Taux de succès (%) |
| `avg_duration_seconds` | Durée moyenne d'exécution |
| `last_duration_seconds` | Dernière durée |
| `total_rows_processed` | Total lignes traitées |
| `data_quality_score` | Score de qualité (0-100) |

### 📌 **État de santé**

```python
# État de santé du pipeline
health = pipeline.health_status

# Valeurs possibles:
# - 'critical' : Échecs consécutifs >= 5
# - 'warning'  : Échecs consécutifs >= 3
# - 'poor'     : Score qualité < 50
# - 'fair'     : Score qualité < 75
# - 'good'     : Tout va bien
```

### 📌 **Statistiques d'exécution**

```python
from apps.etl_engine.models import ExecutionLog

# Dernières 24h
last_24h = ExecutionLog.objects.filter(
    started_at__gte=timezone.now() - timedelta(hours=24)
)

# Taux de succès
success_rate = last_24h.filter(status='completed').count() / last_24h.count() * 100

# Durée moyenne
avg_duration = last_24h.aggregate(Avg('duration_seconds'))['duration_seconds__avg']
```

---

## Notifications

### 📌 **Canaux supportés**

| Canal | Description |
|-------|-------------|
| `email` | Notification par email |
| `slack` | Message Slack via webhook |
| `webhook` | Appel HTTP vers URL personnalisée |
| `teams` | Message Microsoft Teams |
| `sms` | SMS (via service externe) |

### 📌 **Configuration Slack**

```python
notification = PipelineNotification.objects.create(
    pipeline=pipeline,
    channel="slack",
    recipient="#etl-alerts",
    config={
        "webhook_url": "https://hooks.slack.com/services/...",
        "username": "ETL Bot",
        "icon_emoji": ":robot_face:"
    },
    send_on_start=True,
    send_on_success=True,
    send_on_failure=True
)
```

### 📌 **Message type**

```json
{
    "text": "📊 **ETL Pipeline Exécuté**",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Pipeline:* Analyse ventes\n*Statut:* ✅ Succès\n*Durée:* 2m 5s\n*Lignes:* 98,500"
            }
        }
    ]
}
```

---

## Bonnes Pratiques

### ✅ **À FAIRE**

1. **Toujours définir une stratégie d'erreur**
```python
pipeline.error_strategy = "skip"  # Ou "fail", "retry"
```

2. **Utiliser les transformations critiques avec parcimonie**
```python
transformation.is_critical = True  # Arrête le pipeline en cas d'erreur
```

3. **Configurer les notifications pour les échecs**
```python
pipeline.notify_on_failure = True
```

4. **Tester les pipelines avant activation**
```python
pipeline.status = "draft"  # Mode test
# Après validation
pipeline.status = "active"
```

5. **Surveiller les métriques régulièrement**
```python
if pipeline.data_quality_score < 70:
    send_alert(f"Qualité des données faible: {pipeline.name}")
```

### ❌ **À ÉVITER**

1. **Ne pas exécuter de pipelines trop fréquemment** (respecter les limites de la source)
2. **Ne pas ignorer les erreurs de transformation** (utiliser skip ou fail selon le contexte)
3. **Ne pas surcharger avec trop de dépendances** (maintenir un graphe simple)
4. **Ne pas oublier de définir un timeout** (éviter les exécutions infinies)

---

## Exemples d'Utilisation

### 📌 **Pipeline ETL pour l'analyse des ventes**

```python
# 1. Créer le pipeline
pipeline = ETLPipeline.objects.create(
    name="Analyse des ventes quotidienne",
    description="Pipeline quotidien pour l'analyse des ventes",
    pipeline_type="etl",
    source=postgres_source,
    target=warehouse_target,
    schedule_frequency="daily",
    batch_size=50000,
    error_strategy="skip"
)

# 2. Ajouter les transformations
transformations = [
    {
        "order": 1,
        "name": "Filtrer ventes valides",
        "type": "filter",
        "config": {"column": "montant", "operator": "gt", "value": 0}
    },
    {
        "order": 2,
        "name": "Nettoyer les noms",
        "type": "custom_python",
        "custom_code": "df['nom'] = df['nom'].str.strip().str.upper()"
    },
    {
        "order": 3,
        "name": "Agréger par client",
        "type": "aggregate",
        "config": {
            "group_by": ["client_id", "client_nom"],
            "aggregations": {
                "total_ventes": "sum",
                "nb_ventes": "count",
                "moyenne": "avg"
            }
        }
    }
]

for t in transformations:
    Transformation.objects.create(
        pipeline=pipeline,
        order=t["order"],
        name=t["name"],
        transformation_type=t["type"],
        config=t.get("config", {}),
        custom_code=t.get("custom_code", "")
    )

# 3. Configurer le schéma cible
TargetSchema.objects.create(
    pipeline=pipeline,
    table_name="ventes_analyse",
    columns=[
        {"name": "client_id", "type": "INTEGER"},
        {"name": "client_nom", "type": "VARCHAR(255)"},
        {"name": "total_ventes", "type": "DECIMAL(12,2)"},
        {"name": "nb_ventes", "type": "INTEGER"},
        {"name": "moyenne", "type": "DECIMAL(10,2)"}
    ],
    primary_key=["client_id"],
    insert_strategy="upsert",
    upsert_keys=["client_id"]
)

# 4. Configurer les notifications
PipelineNotification.objects.create(
    pipeline=pipeline,
    channel="slack",
    recipient="#etl-alerts",
    send_on_failure=True
)

# 5. Activer le pipeline
pipeline.status = "active"
pipeline.save()
```

### 📌 **Exécution manuelle avec paramètres**

```python
# Exécuter le pipeline pour une date spécifique
result = pipeline.execute(params={
    "date_debut": "2024-01-01",
    "date_fin": "2024-01-31"
})

if result['success']:
    print(f"✅ {result['rows_written']} lignes traitées en {result['duration_seconds']:.1f}s")
else:
    print(f"❌ Erreur: {result['error']}")
```

### 📌 **Orchestration de pipelines dépendants**

```python
# Pipeline A: Extraction des clients
pipeline_a = ETLPipeline.objects.create(name="Extraction clients", ...)

# Pipeline B: Extraction des commandes
pipeline_b = ETLPipeline.objects.create(name="Extraction commandes", ...)

# Pipeline C: Jointure et analyse (dépend de A et B)
pipeline_c = ETLPipeline.objects.create(name="Analyse clients", ...)

# Définir les dépendances
pipeline_c.dependencies.add(pipeline_a, pipeline_b)

# Exécution automatique de A et B avant C
orchestrator = ETLOrchestrator()
result = orchestrator.execute_pipeline(pipeline_c.id)
```

---

## Dépannage

### 🐛 **Problèmes courants**

| Problème | Cause | Solution |
|----------|-------|----------|
| Échec extraction | Source non connectée | Vérifier la source dans Data Sources |
| Timeout | Données trop volumineuses | Augmenter timeout_seconds ou batch_size |
| Transformation échouée | Code Python invalide | Valider le code avec validate_python_code |
| Dépendance cyclique | Pipeline A dépend de B et B dépend de A | Restructurer les dépendances |
| Notification non reçue | Webhook invalide | Vérifier la configuration du canal |

---

## Conclusion

Le module ETL Engine de DataForge offre une solution complète et professionnelle pour l'orchestration de pipelines de données avec :

- 🔄 **8 types de pipelines**
- 🔧 **18+ types de transformations**
- ⏰ **10 fréquences de planification**
- 📊 **Monitoring détaillé**
- 🔔 **Notifications multi-canaux**
- 🚨 **Gestion des erreurs robuste**

---

**Version:** 1.0.0  
**Dernière mise à jour:** 28 Février 2026  
**Mainteneur:** DataForge
```