# DataForge BI Platform

> **Open Source Business Intelligence Platform**  
> Plateforme de Business Intelligence full-stack pour l'analyse de données d'entreprise

---

## Aperçu visuel

### Tableau de bord principal
![Tableau de bord](docs/screenshots/dashboard.png)

### KPIs & Indicateurs
![KPIs](docs/screenshots/kpis.png)

### Pipelines ETL
![Pipelines ETL](docs/screenshots/pipelines.png)

### ML Analytics
![ML Analytics](docs/screenshots/ml-analytics.png)

### Rapports
![Rapports](docs/screenshots/reports.png)

### Connexions aux sources de données
![Connexions](docs/screenshots/connections.png)

### Administration
![Administration](docs/screenshots/admin.png)

---

## Description

**DataForge BI** est une plateforme de Business Intelligence full-stack open source conçue pour centraliser, transformer et visualiser les données métier.

---

## Stack Technique

### Backend
| Technologie | Version | Rôle |
|-------------|---------|------|
| Python | 3.12 | Langage principal |
| Django | 6.0.3 | Framework web |
| Django REST Framework | 3.17.0 | API REST (349 endpoints) |
| PostgreSQL | 18.3 | Base de données principale |
| Simple JWT | 5.5.1 | Authentification JWT (access + refresh) |
| drf-spectacular | 0.29.0 | Documentation OpenAPI 3.0 |
| Celery + Beat | 5.6.2 / 2.9.0 | Tâches planifiées et workflows asynchrones |
| django-import-export | 4.4.0 | Import/export CSV/Excel dans l'admin |
| Jazzmin | 3.0.4 | Thème admin Django professionnel |
| WeasyPrint | 65.1 | Génération de rapports PDF |
| SQLAlchemy | 2.0.41 | Test de connexions multi-SGBD |

### Frontend
| Technologie | Version | Rôle |
|-------------|---------|------|
| Vue 3 | 3.5.34 | Framework UI (Composition API) |
| TypeScript | 6.0.2 | Typage statique |
| Vite | 8.0.12 | Bundler |
| Pinia | 3.0.4 | Gestion d'état |
| Vue Router | 4.6.4 | Routage SPA |
| Axios | 1.16.0 | Client HTTP |
| lucide-vue-next | 1.0.0 | Bibliothèque d'icônes |
| Chart.js | 4.5.1 | Graphiques et visualisations |

### Tests
| Technologie | Version | Rôle |
|-------------|---------|------|
| Playwright | 1.52 | Tests E2E automatisés (86 tests, 0 échec) |

### Infrastructure
| Composant | Détail |
|-----------|--------|
| Serveur | Ubuntu 22.04 LTS |
| IP Backend | 192.168.224.128:8000 |
| Gestionnaire de paquets | uv (Python) + npm (Node) |
| Admin Django | Jazzmin (thème personnalisé DataForge BI) |

---

## Architecture

```
dataforge-bi/
├── dataforge_backend/    # API Django
│   ├── apps/
│   │   ├── core/               # Config système, permissions, pagination
│   │   ├── users/              # Utilisateurs, rôles, équipes
│   │   ├── data_sources/       # Sources de données, connexions DB, fichiers
│   │   ├── data_warehouse/     # Entrepôt, tables de faits/dimensions, mesures
│   │   ├── etl_engine/         # Pipelines ETL, transformations, exécutions
│   │   ├── star_schema/        # Schémas dimensionnels, Galaxy, hiérarchies
│   │   ├── ml_analytics/       # Modèles ML, prévisions, anomalies, segmentation
│   │   ├── visualizations/     # Dashboards, KPIs, rapports, widgets
│   │   └── notifications/      # Alertes, canaux, abonnements
│   └── config/                 # Settings, URLs, WSGI
├── dataforge_frontend/     # SPA Vue 3
│   └── src/
│       ├── views/              # 22 pages complètes
│       ├── stores/             # Pinia (auth)
│       ├── router/             # Vue Router
│       ├── api/                # Axios instance
│       └── assets/             # Design system (CSS tokens)
├── tests/                      # Tests E2E Playwright
│   └── e2e/                    # 87 tests (86 passing, 1 skipped)
└── docs/
    └── screenshots/            # Captures d'écran des pages clés
```

---

## Fonctionnalités

### Backend — 8 applications Django, 77+ modèles, 349 endpoints REST

| Application | Modèles clés | Endpoints |
|-------------|-------------|-----------|
| `users` | User, Role, Team, Permission | CRUD complet + toggle status |
| `data_sources` | DataSource, DataSourceConnection, DataSourceFile | CRUD + test connexion + upload |
| `data_warehouse` | FactTable, DimensionTable, Measure, AggregationTable | CRUD + stats |
| `etl_engine` | Pipeline, Transformation, Execution | CRUD + run + preview |
| `star_schema` | DimensionalSchema, GalaxySchema, DimensionHierarchy | CRUD complet |
| `ml_analytics` | MLModel, Forecast, Anomaly, Recommendation | Training + inférence |
| `visualizations` | Dashboard, KPI, Report, Widget, Favorite | CRUD + generate + export |
| `notifications` | AlertRule, NotificationChannel, Subscription | CRUD + test + envoi |

### Frontend — 22 pages Vue 3

| Page | Route | Fonctionnalités |
|------|-------|-----------------|
| Login | `/login` | Auth JWT avec validation |
| Dashboard | `/dashboard` | Vue d'ensemble KPIs, pipelines, alertes |
| Sources | `/sources` | Gestion des sources de données |
| Connexions | `/sources/connections` | Connexions multi-SGBD avec test live |
| Fichiers | `/sources/files` | Upload, traitement, prévisualisation |
| Pipelines ETL | `/pipelines` | CRUD pipelines + exécution en temps réel |
| Entrepôt | `/warehouse` | Tables de faits/dimensions + mesures |
| Star Schema | `/star-schema` | Schémas dimensionnels visuels |
| ML Analytics | `/ml-analytics` | Modèles, prévisions, anomalies |
| Dashboards | `/dashboards` | Tableaux de bord interactifs |
| KPIs | `/kpis` | Indicateurs avec sparklines et tendances |
| Rapports | `/reports` | Génération PDF/CSV avec planification |
| Admin | `/admin` | Gestion users, rôles, équipes |
| Notifications | `/notifications` | Alertes et canaux de notification |
| Favoris | `/favorites` | Éléments favoris |
| Exécutions | `/executions` | Historique des exécutions ETL |

---

## Tests E2E — Résultats Playwright

```
87 tests — 86 passed — 1 skipped — 0 failed
```

| Suite | Tests | Statut |
|-------|-------|--------|
| Authentification | 2 | ✅ |
| Sources de données | 8 | ✅ |
| Connexions DB | 9 | ✅ |
| Fichiers | 12 | ✅ |
| KPIs | 9/10 | ✅ (1 skip) |
| Dashboards | 9 | ✅ |
| Rapports | 13 | ✅ |
| Administration | 11 | ✅ |
| Navigation | 6 | ✅ |
| Dashboard général | 7 | ✅ |

---

## Design System

| Token | Valeur |
|-------|--------|
| Font UI | Figtree |
| Font titres | Barlow Condensed |
| Couleur accent | `oklch(76% 0.14 62)` — ambre chaud |
| Surfaces | Navy-slate sombre |
| Mode | Dark uniquement |

---

## Démarrage rapide

### Backend
```bash
cd dataforge_backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000
```

### Frontend
```bash
cd dataforge_frontend
npm install
npm run dev
```

### Tests E2E
```bash
cd tests
npx playwright install --with-deps chromium
npx playwright test
```

### Admin Django
- URL : `http://192.168.224.128:8000/admin/`
- Documentation API : `http://192.168.224.128:8000/api/schema/swagger-ui/`

---

## Endpoints API principaux

### Authentification
| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/auth/jwt/token/` | Obtenir access + refresh token |
| POST | `/api/auth/jwt/refresh/` | Rafraîchir le token |

### Préfixes
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

*DataForge BI — Open Source — Djafar Ahmat Mahamat Moussa, 2026*
