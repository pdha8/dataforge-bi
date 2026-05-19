# DataForge BI — Backend Django

API REST de la plateforme **DataForge BI** (Django 6 + DRF + PostgreSQL), une plateforme BI open source.

🌐 **API en production** : [dataforge-api.onrender.com](https://dataforge-api.onrender.com)
📖 **Documentation OpenAPI** : [dataforge-api.onrender.com/api/docs/](https://dataforge-api.onrender.com/api/docs/) (Swagger UI)

---

## Aperçu

Backend organisé en **9 apps Django** couvrant l'ensemble du cycle BI : ingestion (sources de données), transformation (ETL), modélisation dimensionnelle (data warehouse + star schema), restitution (visualisations, KPI, rapports), analyse prédictive (ML), notifications et administration des utilisateurs.

**349 endpoints REST** exposés via Django REST Framework, **272 schémas OpenAPI** auto-documentés via drf-spectacular, authentification JWT (access + refresh), gestion fine des permissions par rôle.

---

## Stack technique

| Composant | Version | Rôle |
|---|---|---|
| **Python** | 3.13 | Langage |
| **Django** | 6.0 | Framework web |
| **Django REST Framework** | 3.17 | API REST |
| **simplejwt** | 5.5 | Authentification JWT |
| **drf-spectacular** | 0.29 | Documentation OpenAPI 3.0 |
| **drf-yasg** | 1.21 | Swagger UI (compatibilité) |
| **PostgreSQL** | 16+ | Stockage transactionnel + warehouse |
| **SQLAlchemy** | 2.0 | Test multi-SGBD |
| **Pandas** | 3.0 | Transformations tabulaires (ETL) |
| **Prophet** | 1.3 | Prévisions séries temporelles |
| **scikit-learn** | 1.8 | Algorithmes ML (clustering, classification, anomalies) |
| **XGBoost** | 3.2 | Modèles d'ensemble |
| **Celery + Redis** | 5.6 | Tâches asynchrones (entraînement ML, envoi notifications) |
| **Gunicorn** | 26.0 | Serveur WSGI prod |
| **Jazzmin** | 3.0 | Thème de l'admin Django |

---

## Architecture

```
dataforge_backend/
├── config/                        # Configuration projet
│   ├── settings/                  # Settings (base, dev, prod)
│   ├── urls.py                    # Routing principal
│   ├── wsgi.py / asgi.py
│   └── celery.py
├── apps/
│   ├── core/                      # Réponses standardisées, helpers, signaux
│   ├── users/                     # Auth JWT, User, rôles, équipes, permissions
│   ├── data_sources/              # Sources, connexions, queries, fichiers
│   ├── etl_engine/                # Pipelines, transformations, exécutions
│   ├── data_warehouse/            # Schémas, tables faits/dim, mesures, agrégations
│   ├── star_schema/               # Schémas dimensionnels, galaxies, hiérarchies
│   ├── visualizations/            # Dashboards, widgets, KPI, rapports, favoris
│   ├── notifications/             # Notifications, règles d'alerte, canaux
│   └── ml_analytics/              # Modèles ML, prévisions, anomalies, segmentation
├── docs/                          # Documentation technique (voir docs/README.md)
├── manage.py
├── build.sh                       # Script Render (deps + collectstatic + migrate)
├── seed_data.py                   # Données de démo
└── requirements.txt
```

---

## Démarrage rapide (local)

### Prérequis
- Python 3.13 (`pyenv install 3.13.7`)
- PostgreSQL 16+ ou SQLite (par défaut en local)
- (Optionnel) Redis pour Celery

### Installation
```bash
# Cloner et entrer dans le dossier
git clone https://github.com/pdha811/dataforge-bi.git
cd dataforge-bi/dataforge_backend

# Environnement virtuel
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate sur Windows

# Dépendances
pip install -r requirements.txt
```

### Variables d'environnement
Créer un fichier `.env` à la racine de `dataforge_backend/` :
```env
SECRET_KEY=ton_secret_django_50+_caracteres
DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/dataforge_db
# OU pour SQLite local :
# DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Migrations et seed
```bash
python manage.py migrate
python manage.py createsuperuser
python seed_data.py        # données de démo (sources, pipelines, KPI, etc.)
```

### Lancer le serveur
```bash
python manage.py runserver 0.0.0.0:8000
```

- API : http://localhost:8000/api/
- Admin Django : http://localhost:8000/admin/
- Swagger UI : http://localhost:8000/api/docs/
- ReDoc : http://localhost:8000/api/redoc/

---

## Comptes de démonstration (prod)

| Rôle | Email | Mot de passe |
|---|---|---|
| Superadmin | admin@dataforge.tech | `DataForge@2026!` |
| Développeur BI | dev.bi@dataforge.tech | `DataForge@2026!` |
| Analyste BI | analyste@dataforge.tech | `DataForge@2026!` |
| Direction | direction@dataforge.tech | `DataForge@2026!` |

---

## Modules / apps

| App | Modèles principaux | Endpoints REST |
|---|---|---|
| **users** | User, Role, Team, UserActivity | `/api/users/...` (~40 endpoints) |
| **data_sources** | DataSource, DataQuery, PowerQuery, DataSourceConnection, DataSourceFile | `/api/data-sources/...` (~65 endpoints) |
| **etl_engine** | ETLPipeline, Transformation, ExecutionLog, PipelineNotification | `/api/etl/...` (~48 endpoints) |
| **data_warehouse** | DataWarehouseSchema, FactTable, DimensionTable, Measure, AggregationTable | `/api/data-warehouse/...` (~73 endpoints) |
| **star_schema** | DimensionalSchema, GalaxySchema, FactRelationship, DimensionHierarchy, CustomCalculation | `/api/star-schema/...` (~37 endpoints) |
| **visualizations** | Dashboard, Widget, KPI, Report, Favorite | `/api/visualizations/...` (~50 endpoints) |
| **notifications** | Notification, AlertRule, NotificationChannel, Subscription | `/api/notifications/...` (~33 endpoints) |
| **ml_analytics** | MLModel, Forecast, Anomaly, SegmentationResult, Recommendation | `/api/ml-analytics/...` |

---

## Authentification

### Obtenir un access token
```bash
curl -X POST https://dataforge-api.onrender.com/api/auth/jwt/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dataforge.tech","password":"DataForge@2026!"}'
```
Renvoie `{ "access": "...", "refresh": "..." }`.

### Utiliser le token
```bash
curl https://dataforge-api.onrender.com/api/users/users/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Rafraîchir
```bash
curl -X POST https://dataforge-api.onrender.com/api/auth/jwt/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<REFRESH_TOKEN>"}'
```

---

## Format de réponse

### Endpoints `@action` custom
Wrappés via `apps.core.responses.success_response()` :
```json
{
  "status": true,
  "message": "Opération réussie",
  "data": { ... },
  "timestamp": "2026-05-17T11:03:28Z"
}
```

### Endpoints CRUD standard (ModelViewSet list/create/retrieve/update/destroy)
JSON DRF brut, non wrapped — directement la ressource ou la pagination DRF.

### Erreurs
```json
{
  "status": false,
  "message": "Erreur de validation.",
  "errors": { "champ": ["message"] },
  "code": "bad_request"
}
```

### Pagination
```json
{
  "status": true,
  "count": 42,
  "total_pages": 5,
  "current_page": 1,
  "next": "...",
  "previous": null,
  "results": [ ... ]
}
```

---

## Tests

### Tests E2E (TestSprite MCP)
La suite de tests automatisée — frontend (E2E) + backend (API directe) — est gérée au niveau projet. Voir `../TESTING_REPORT.md`.

**Score actuel :**
- Frontend E2E : **28 / 30 (93,3 %)**
- Backend API : **7 / 10 (70 %)** sur la suite générée

### Tests manuels
```bash
python manage.py test apps        # tests Django classiques (si disponibles)
```

### Smoke test
```bash
curl https://dataforge-api.onrender.com/api/health/
# → {"status": "ok", "service": "dataforge-api"}
```

---

## Déploiement sur Render

### Configuration Web Service
- **Region** : Frankfurt EU Central
- **Plan** : Free (512 Mo RAM, 0.1 CPU)
- **Root Directory** : `dataforge_backend`
- **Build Command** : `./build.sh`
- **Start Command** :
  ```
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT \
    --workers 1 --threads 4 --timeout 120 --preload \
    --max-requests 500 --max-requests-jitter 50
  ```
- **Health Check Path** : `/api/health/`

### Variables d'environnement requises
| Variable | Description |
|---|---|
| `DATABASE_URL` | Injecté automatiquement par Render PostgreSQL |
| `SECRET_KEY` | Clé Django (≥ 50 caractères aléatoires) |
| `ALLOWED_HOSTS` | `dataforge-api.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | `https://dataforge-app.onrender.com` |
| `DJANGO_SUPERUSER_EMAIL` | Email superadmin (créé au 1er build) |
| `DJANGO_SUPERUSER_PASSWORD` | Mot de passe superadmin |
| `RUN_SEED` | `1` au premier déploiement uniquement, à retirer ensuite |

### Choix critiques pour le plan Free
- **`--workers 1 --preload`** : les libs ML (prophet, xgboost, sklearn, scipy, pandas) pèsent ~400 Mo chacune si dupliquées. Avec preload, le master charge tout une fois, puis fork. Sans cette config → OOM garanti.
- **`CompressedStaticFilesStorage`** au lieu de `ManifestStaticFilesStorage` : Jazzmin et drf-yasg référencent des assets qui peuvent manquer ; la variante Manifest casse tout le serve statique sur un hash manquant.
- **Redirection `/` → `/admin/`** : le health-checker Render poll `/` ; sans route racine → 404 → service unhealthy.

---

## Documentation détaillée

Voir le dossier `docs/` :
- [Architecture overview](docs/architecture/overview.md)
- [Data flow](docs/architecture/data-flow.md)
- [Security](docs/architecture/security.md)
- [API endpoints](docs/api/endpoints.md)
- [Authentication](docs/api/authentication.md)
- [Errors](docs/api/errors.md)
- [Setup](docs/development/setup.md)
- [Contributing](docs/development/contributing.md)
- [Testing](docs/development/testing.md)
- Modules : core, users, data_sources, etl_engine, data_warehouse, star_schema, visualizations

---

*DataForge BI — Open Source — Djafar Ahmat Mahamat Moussa, 2026*
