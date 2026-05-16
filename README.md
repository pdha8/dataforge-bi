# Integrated BI Platform — Sotifibre

> **Projet de Fin d'Études (PFE) — 2026**
> Plateforme de Business Intelligence complète pour l'analyse de données d'entreprise

---

## Aperçu

**Integrated BI** est une plateforme de Business Intelligence full-stack conçue pour centraliser, transformer et visualiser les données métier de SOTIFibre. Elle couvre l'ensemble du cycle de vie de la donnée : ingestion, transformation ETL, modélisation dimensionnelle, visualisation, alertes et rapports automatisés.

---

## Stack Technique

### Backend
| Technologie | Version | Rôle |
|-------------|---------|------|
| Python | 3.12 | Langage principal |
| Django | 6.0.3 | Framework web |
| Django REST Framework | 3.15 | API REST (349 endpoints) |
| PostgreSQL | 18.x | Base de données principale |
| Simple JWT | 5.x | Authentification JWT (access + refresh) |
| drf-spectacular | 0.27 | Documentation OpenAPI 3.0 |
| Celery + Beat | 5.x | Tâches planifiées et workflows asynchrones |
| django-import-export | 4.x | Import/export CSV/Excel dans l'admin |
| Jazzmin | 3.x | Thème admin Django professionnel |

### Frontend
| Technologie | Version | Rôle |
|-------------|---------|------|
| Vue 3 | 3.5 | Framework UI (Composition API) |
| TypeScript | 5.7 | Typage statique |
| Vite | 6.x | Bundler |
| Pinia | 2.x | Gestion d'état |
| Vue Router | 4.x | Routage SPA |
| Axios | 1.x | Client HTTP |
| lucide-vue-next | 0.x | Bibliothèque d'icônes |
| Chart.js | 4.x | Graphiques et visualisations |

### Infrastructure
| Composant | Détail |
|-----------|--------|
| Serveur | Ubuntu 22.04 LTS |
| IP Backend | 192.168.224.128:8000 |
| Gestionnaire de paquets | uv (Python) + npm (Node) |
| Admin Django | Jazzmin (thème personnalisé SOTIFibre) |

---

## Architecture

```
Integrated_BI/
├── sotifibre_backend_django/    # API Django
│   ├── apps/
│   │   ├── core/               # Config système
│   │   ├── users/              # Utilisateurs, rôles, équipes
│   │   ├── data_sources/       # Sources de données, connexions DB, fichiers
│   │   ├── data_warehouse/     # Entrepôt, tables de faits/dimensions, mesures
│   │   ├── etl_engine/         # Pipelines ETL, transformations, exécutions
│   │   ├── star_schema/        # Schémas dimensionnels, Galaxy, hiérarchies
│   │   ├── ml_analytics/       # Modèles ML, prévisions, anomalies
│   │   ├── visualizations/     # Dashboards, KPIs, rapports, widgets
│   │   └── notifications/      # Alertes, canaux, abonnements
│   └── config/                 # Settings, URLs, WSGI
└── integrated-bi-frontend/     # SPA Vue 3
    └── src/
        ├── views/              # 22 pages complètes
        ├── stores/             # Pinia (auth)
        ├── router/             # Vue Router
        ├── api/                # Axios instance
        └── assets/             # Design system (CSS tokens)
```

---

## Fonctionnalités

### Backend — 8 applications Django, 77+ modèles, 349 endpoints REST

| Application | Modèles clés |
|-------------|-------------|
| `core` | Config système |
| `users` | User, Role, Team, AuditLog |
| `data_sources` | DataSource, DataTable, Connection, DataFile |
| `data_warehouse` | DataWarehouseTable (FactTable/DimensionTable proxy), Measure, Aggregation |
| `etl_engine` | ETLPipeline, Transformation, Execution, SourceSchema, TargetSchema |
| `star_schema` | DimensionalSchema, GalaxySchema, FactRelationship, DimensionHierarchy, CustomCalculation |
| `ml_analytics` | MLModel, Forecast, Anomaly, SegmentationResult, Recommendation, ModelTrainingLog |
| `visualizations` | Dashboard, Widget, KPI, Report, Favorite, VisualizationActivity |
| `notifications` | Notification, AlertRule, NotificationChannel, Subscription |

### Frontend — 22 pages complètes

| # | Page | Route | Description |
|---|------|-------|-------------|
| 1 | Login | `/login` | Authentification JWT |
| 2 | Dashboard | `/` | KPIs temps réel + graphiques |
| 3 | Sources de données | `/sources` | CRUD sources + tables de données |
| 4 | Monitoring source | `/sources/:id/monitoring` | Logs + métriques de synchronisation |
| 5 | Power Queries | `/sources/power-queries` | Requêtes visuelles avancées |
| 6 | Requêtes SQL | `/sources/queries` | Éditeur SQL interactif |
| 7 | Connexions DB | `/sources/connections` | CRUD connexions base de données + test |
| 8 | Fichiers de données | `/sources/files` | Upload, prévisualisation, traitement |
| 9 | Pipelines ETL | `/pipelines` | Orchestration ETL complète |
| 10 | Exécutions ETL | `/executions` | Historique et monitoring des runs |
| 11 | Data Warehouse | `/warehouse` | Explorer tables faits/dimensions + agrégations |
| 12 | Schémas étoile | `/star-schema` | Modélisation dimensionnelle + Galaxy |
| 13 | ML Analytics | `/ml-analytics` | Modèles, prévisions, anomalies, recommandations |
| 14 | Visualisations | `/visualizations` | Galerie de visualisations |
| 15 | Tableaux de bord | `/dashboards` | Dashboards + widgets |
| 16 | KPIs | `/kpis` | Indicateurs clés de performance |
| 17 | Rapports | `/reports` | Génération et planification CRON |
| 18 | Notifications | `/notifications` | Alertes, canaux, abonnements |
| 19 | Administration | `/admin` | Utilisateurs, rôles, équipes, audit |
| 20 | Profil | `/profile` | Profil utilisateur |
| 21 | Favoris | `/favorites` | Favoris personnels |
| 22 | Système | (dans Admin) | Liens admin Django, Celery Beat |

---

## Design System

| Token | Valeur |
|-------|--------|
| Font UI | Figtree |
| Font titres | Barlow Condensed |
| Couleur accent | oklch(76% 0.14 62) — ambre chaud |
| Surfaces | Navy-slate sombre |

---

## Démarrage rapide

### Backend
```bash
cd sotifibre_backend_django
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

### Frontend
```bash
cd integrated-bi-frontend
npm install
npm run dev
```

### Admin Django
- URL : http://192.168.224.128:8000/admin/
- Documentation API : http://192.168.224.128:8000/api/schema/swagger-ui/

---

## Endpoints API

### Authentification
| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/auth/jwt/token/` | Obtenir access + refresh token |
| POST | `/api/auth/jwt/refresh/` | Rafraîchir le token |

### Principaux préfixes
| Préfixe | Application |
|---------|-------------|
| `/api/users/` | Utilisateurs, rôles, équipes |
| `/api/data-sources/` | Sources, connexions, fichiers, tables |
| `/api/etl/` | Pipelines, transformations, exécutions |
| `/api/data-warehouse/` | Entrepôt de données |
| `/api/star-schema/` | Schémas dimensionnels |
| `/api/ml-analytics/` | Analyses ML |
| `/api/visualizations/` | Dashboards, KPIs, rapports |
| `/api/notifications/` | Alertes et notifications |

---

## Captures d'écran

Toutes les captures sont automatiquement générées par la suite Playwright
(`tests/e2e/screenshots.spec.ts`). Pour les régénérer :

```bash
cd tests
npm run test:e2e -- e2e/screenshots.spec.ts
```

### Module Sources de données
| | |
|---|---|
| ![Sources de données](docs/screenshots/sources.png) <br>**Sources** — vue maître | ![Fichiers](docs/screenshots/sources-files.png) <br>**Fichiers** — upload (6 formats standards) |
| ![Connexions](docs/screenshots/sources-connections.png) <br>**Connexions DB** | ![Monitoring](docs/screenshots/sources-monitoring.png) <br>**Monitoring** — logs + bouton « Nouvelle requête » |
| ![Power Queries](docs/screenshots/power-queries.png) <br>**Power Queries** | ![Requêtes SQL](docs/screenshots/queries.png) <br>**Éditeur SQL** |

### Module ETL et Data Warehouse
| | |
|---|---|
| ![Pipelines](docs/screenshots/pipelines.png) <br>**Pipelines** — auto-nom Source → Destination | ![Exécutions](docs/screenshots/executions.png) <br>**Historique des exécutions** |
| ![Data Warehouse](docs/screenshots/warehouse.png) <br>**Data Warehouse** — Explorer / Faits / Agrégations / Monitoring | ![Schémas en étoile](docs/screenshots/star-schema.png) <br>**Schémas en étoile** — Galaxies, Calculs, Hiérarchies |
| ![ML Analytics](docs/screenshots/ml-analytics.png) <br>**ML Analytics** — modèles, entraînement, prédictions | |

### Module Visualisation et Reporting
| | |
|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) <br>**Dashboard d'accueil** | ![Tableaux de bord](docs/screenshots/dashboards.png) <br>**Dashboards** — CRUD + drawer Widgets |
| ![Visualisations](docs/screenshots/visualizations.png) <br>**Visualisations** — sélecteur Dashboard dynamique | ![KPIs](docs/screenshots/kpis.png) <br>**KPIs** — cibles + seuils warning/critical |
| ![Rapports](docs/screenshots/reports.png) <br>**Rapports** — multi-select destinataires + HTML (WeasyPrint) | |

### Module Système
| | |
|---|---|
| ![Favoris](docs/screenshots/favorites.png) <br>**Favoris** — étoile sur Reports/Viz/KPIs | ![Notifications](docs/screenshots/notifications.png) <br>**Notifications** — 4 onglets |
| ![Administration](docs/screenshots/admin.png) <br>**Administration** — 7 onglets dont Journal d'audit | ![Profil](docs/screenshots/profile.png) <br>**Profil** |

---

## Tests E2E (Playwright)

5 suites Playwright couvrant les 4 modules métier + le système.
Tous les tests s'exécutent en headless par défaut et en `--headed` pour la
démonstration visuelle.

```bash
cd tests
npm install
npx playwright install chromium
npm run test:e2e                            # toutes les suites, headless
npx playwright test --headed --workers=1    # toutes les suites, visibles
npx playwright test e2e/analytics-dashboards.spec.ts --headed
```

| Suite | Fichier | Couverture |
|---|---|---|
| Analytics — Dashboards / Viz / KPIs / Reports | `e2e/analytics-dashboards.spec.ts` | 19 tests |
| Data Sources | `e2e/data-sources.spec.ts` | 16 tests |
| Pipelines ETL | `e2e/pipelines-etl.spec.ts` | 10 tests |
| Data Warehouse + Star Schema + ML | `e2e/data-warehouse.spec.ts` | 13 tests |
| Système (Favoris, Notifications, Admin, Profil, Sidebar) | `e2e/system-favorites.spec.ts` | 16 tests |
| Captures d'écran | `e2e/screenshots.spec.ts` | 20 captures |

**Identifiants de test** :
```
TEST_USER_EMAIL=admin@sotifibre.dz
TEST_USER_PASSWORD=SOTIFibre@2026!
```

---

## Conformité au cahier des charges PFE

Les 7 exigences du cahier des charges sont couvertes et vérifiées par les
suites Playwright :

| # | Exigence cahier des charges | Implémentation | Vérification E2E |
|---|---|---|---|
| 1 | **Intégration de sources multiples** (CSV, Excel, DB, API) | 6 formats fichiers (`xlsx, csv, yaml, json, tsv, html`) + 16 types de DB + REST/GraphQL/SOAP/OData + Cloud (S3/Azure/GCS) + Streaming (Kafka/Kinesis) | `data-sources.spec.ts` — upload CSV, accept des 6 formats |
| 2 | **Processus ETL configurable** (filtrage, regroupement, calcul) | `etl_engine` : 22 types de transformations, modes (batch/streaming/incremental/full), stratégies d'erreur (fail/skip/default/retry/notify/continue) | `pipelines-etl.spec.ts` — CRUD pipeline, alignement choices backend |
| 3 | **Data Warehouse en étoile** (faits + dimensions) | `data_warehouse` (FactTable, DimensionTable, Measure, Aggregation) + `star_schema` (DimensionalSchema, GalaxySchema, FactRelationship, Hierarchy) | `data-warehouse.spec.ts` — 4 onglets Warehouse + 5 onglets Schema |
| 4 | **Visualisations interactives** (graphiques dynamiques) | Chart.js (Line/Bar/Doughnut/Scatter) + sparklines KPI + canvas/svg | `analytics-dashboards.spec.ts` — détection `<canvas>` / `<svg>` |
| 5 | **Tableaux de bord personnalisables** (filtres globaux) | 8 layouts (hero3, twoRow, kpiRow, bigLeft, triple, classic, magazine, minimal) + drawer CRUD + widgets-tab + sélecteur Dashboard dynamique sur les viz | `analytics-dashboards.spec.ts` — Dashboards CRUD, Widgets onglet |
| 6 | **Indicateurs (KPIs)** avec cibles et alertes | `KPI` model : `target_value`, `warning_threshold`, `critical_threshold` + endpoints `/critical/` `/warning/` + statuts CSS dynamiques | `analytics-dashboards.spec.ts` — création KPI avec seuils, filtres |
| 7 | **Sécurité et gestion des rôles** (JWT strict) | Simple JWT (access + refresh + auto-renew) + 7 permissions (canManage*) + 3 rôles (superadmin/admin/user) + 7 sous-sections admin dont Journal d'audit | `system-favorites.spec.ts` — admin 7 onglets, profil, audit filters |

### Corrections appliquées pendant le QA

| Domaine | Bug détecté | Fix |
|---|---|---|
| Visualizations | Champ « Source de données » en saisie libre (`Ex : DW_VENTES.fact_ventes`) | Remplacé par `<select>` Dashboard dynamique branché sur `/api/visualizations/dashboards/` |
| Source Monitoring | Logs sans `query_text` affichaient « Aucune requête associée à ce log » sans action | Bouton **Nouvelle requête** qui ouvre `/queries?open=new&source=…&hint=…&from_log=…` avec préfilage SQL automatique |
| Pipelines | `payload.destination` envoyé au backend qui attend `target` ; choices asymétriques (`full_load`/`fail_fast`/`sequential`/`priority='medium'`) | Renommage `destination → target` + alignement complet : `etl/batch/fail/priority:5` |
| Pipelines UX | Nom du pipeline à taper manuellement avec la flèche `→` | Auto-génération `Source → Destination` à partir des selects (préservation des saisies manuelles) |
| Favoris | Aucun bouton « étoile » sur Reports/Visualizations/KPIs | Ajouté sur les 3 pages avec POST `/api/visualizations/favorites/add/remove/` |
| Star Schema | Bouton « Valider le schéma » → 405 (backend en GET uniquement) | `@action(methods=['get', 'post'])` pour accepter le clic UI |
| Formats | `EXPORT_FORMATS` contenait `pdf` (sortait des 6 formats standards) | Migration 0005 : conversion `pdf → html` + choices strictement 6 formats |
| Backend | Sérialiseur `DataQueryCreateSerializer` dupliqué dans `serializers.py` | Doublon supprimé |

### Suite QA — chiffres clés

- **74 tests E2E** Playwright (5 suites)
- **~95 % de réussite** (échec restant : `validate POST` qui nécessite redéploiement backend du fix `views.py`)
- **21 captures d'écran** générées automatiquement
- **1 migration Django** (`0005_export_formats_strict_6`) à appliquer pour finaliser

---

*Réalisé dans le cadre du PFE — Abdoulaye Adoum, 2026*
