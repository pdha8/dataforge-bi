# Integrated BI Platform — Sotifibre

> **Projet de Fin d'Etudes (PFE) — 2026**
> Plateforme de Business Intelligence complete pour l'analyse de donnees d'entreprise

---

## Apercu

**Integrated BI** est une plateforme de Business Intelligence full-stack concue pour centraliser, transformer et visualiser les donnees metier de Sotifibre. Elle couvre l'ensemble du cycle de vie de la donnee : ingestion, transformation ETL, modelisation dimensionnelle, visualisation, alertes et rapports automatises.

---

## Stack Technique

### Backend
| Technologie | Version | Role |
|-------------|---------|------|
| Python | 3.12 | Langage principal |
| Django | 5.x | Framework web |
| Django REST Framework | 3.x | API REST |
| PostgreSQL | 18.3 | Base de donnees principale |
| Simple JWT | — | Authentification JWT |
| drf-spectacular | — | Documentation OpenAPI 3.0 |
| Celery Beat | — | Taches planifiees |

### Frontend
| Technologie | Version | Role |
|-------------|---------|------|
| Vue 3 | 3.x | Framework UI |
| TypeScript | 5.x | Typage statique |
| Vite | 5.x | Bundler |
| Pinia | 2.x | Gestion d'etat |
| Vue Router | 4.x | Routage SPA |
| Axios | 1.x | Client HTTP |
| Lucide Vue | — | Icones |
| Chart.js | 4.x | Graphiques |

### Infrastructure
| Composant | Detail |
|-----------|--------|
| Serveur | Ubuntu 24.04 LTS |
| Reverse Proxy | Nginx 1.24 |
| Base de donnees | PostgreSQL 18.3 |

---

## Architecture

```
Navigateur Client
       |  HTTP :80
       v
Nginx (Reverse Proxy)
  /          --> Vue 3 SPA  (/var/www/integrated-bi)
  /api/*     --> Django Backend (:8000)
  /admin/    --> Django Admin (:8000)
       |
       v
Django Backend (:8000)
  apps/
  |-- users/          Authentification et Equipes
  |-- data_sources/   Sources de donnees
  |-- etl_engine/     Pipelines ETL
  |-- data_warehouse/ Entrepot de donnees
  |-- star_schema/    Schemas dimensionnels
  |-- visualizations/ KPIs, Dashboards, Widgets
  |-- notifications/  Alertes et Canaux
  |-- core/           Configuration globale
       |
       v
PostgreSQL 18.3 — sotifibre_db
83 tables  •  79 migrations appliquees
```

---

## Fonctionnalites

### Donnees
- **Sources de donnees** — Connexion multi-sources (PostgreSQL, MySQL, CSV, Excel, API REST, FTP) avec synchronisation et monitoring
- **Pipelines ETL** — Creation, planification et monitoring des pipelines de transformation avec journal d'execution
- **Surveillance ETL** — Vue globale de toutes les executions en temps reel avec filtres par statut, pipeline et declencheur
- **Data Warehouse** — Gestion des tables de dimensions et de faits avec rafraichissement, analyse et optimisation

### Modelisation
- **Schemas en etoile** — Modelisation dimensionnelle : schemas etoile, flocon, galaxie, constellation
- **Calculs personnalises** — Formules et indicateurs derives
- **Hierarchies de dimensions** — Organisation hierarchique des attributs

### Analytique
- **Visualisations** — Graphiques interactifs : courbe, barres, circulaire, nuage de points, aires, tableau
- **Tableaux de bord** — Creation, partage et publication de dashboards personnalises
- **KPIs** — Suivi des indicateurs cles avec barre de progression, sparkline et calcul automatique
- **Rapports** — Generation planifiee (CRON) en PDF, Excel, CSV, JSON avec envoi automatique

### Systeme
- **Notifications** — Centre de notifications avec regles d'alerte et canaux (Email, SMS, Webhook, Slack)
- **Administration** — Gestion des utilisateurs, roles, equipes et parametres systeme
- **Audit** — Journal d'activite complet

---

## Structure du Projet

```
Integrated_BI/
|-- sotifibre_backend_django/       # Backend Django
|   |-- apps/
|   |   |-- users/                  # Utilisateurs et authentification
|   |   |-- data_sources/           # Sources de donnees et requetes
|   |   |-- etl_engine/             # Moteur ETL et executions
|   |   |-- data_warehouse/         # Entrepot de donnees
|   |   |-- star_schema/            # Modelisation dimensionnelle
|   |   |-- visualizations/         # Visualisations, KPIs, Dashboards
|   |   |-- notifications/          # Notifications et alertes
|   |   |-- core/                   # Configuration commune
|   |-- config/
|   |   |-- settings/               # Parametres (base, dev, prod)
|   |   |-- urls.py                 # Routes principales
|   |-- manage.py
|
|-- integrated-bi-frontend/         # Frontend Vue 3 TypeScript
|   |-- src/
|   |   |-- views/                  # 12 pages de l'application
|   |   |   |-- dashboard/          # Tableau de bord principal
|   |   |   |-- sources/            # Sources de donnees
|   |   |   |-- pipelines/          # Pipelines ETL
|   |   |   |-- executions/         # Monitoring des executions
|   |   |   |-- warehouse/          # Data Warehouse
|   |   |   |-- star-schema/        # Schemas dimensionnels
|   |   |   |-- visualizations/     # Graphiques et widgets
|   |   |   |-- dashboards/         # Tableaux de bord
|   |   |   |-- kpis/               # Indicateurs cles
|   |   |   |-- reports/            # Rapports automatises
|   |   |   |-- notifications/      # Centre de notifications
|   |   |   |-- admin/              # Administration
|   |   |-- components/             # Header, Sidebar
|   |   |-- stores/                 # Pinia (authentification)
|   |   |-- router/                 # Vue Router (12 routes)
|   |   |-- api/                    # Client Axios avec JWT
|
|-- .gitignore
|-- README.md
```

---

## Installation

### Prerequis
- Python 3.12+ avec `uv`
- PostgreSQL 18
- Node.js 20+ et npm

### 1. Backend Django

```bash
git clone https://github.com/Adoum-Cyber/Integrated_BI.git
cd Integrated_BI/sotifibre_backend_django

uv sync
cp .env.example .env
# Editer .env avec vos parametres

uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver 0.0.0.0:8000
```

### 2. Frontend Vue 3

```bash
cd Integrated_BI/integrated-bi-frontend

npm install
npm run dev        # Developpement  (port 5173)
npm run build      # Build production
```

### 3. Variables d'environnement (`.env`)

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip

DB_ENGINE=django.db.backends.postgresql
DB_NAME=sotifibre_db
DB_USER=sotifibre_admin
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOW_ALL_ORIGINS=True
```

---

## Deploiement Production

```bash
# Build et copie vers Nginx
cd integrated-bi-frontend
npm run build
sudo cp -r dist/* /var/www/integrated-bi/
sudo systemctl reload nginx
```

| URL | Service |
|-----|---------|
| `http://server-ip/` | Frontend Vue 3 |
| `http://server-ip/api/` | API REST Django |
| `http://server-ip:8000/api/schema/swagger-ui/` | Documentation Swagger |
| `http://server-ip:8000/admin/` | Interface Django Admin |

---

## Documentation API

API REST documentee en **OpenAPI 3.0** — **349 endpoints** sur 9 modules :

| Module | Endpoint | Description |
|--------|----------|-------------|
| Auth | `/api/auth/jwt/token/` | Authentification JWT (email + password) |
| Utilisateurs | `/api/users/` | Gestion utilisateurs, roles, equipes |
| Sources | `/api/data-sources/` | Connexions aux sources de donnees |
| ETL | `/api/etl/` | Pipelines et executions |
| Warehouse | `/api/data-warehouse/` | Tables de dimensions et faits |
| Schemas | `/api/star-schema/` | Modelisation dimensionnelle |
| Visualisations | `/api/visualizations/` | KPIs, dashboards, widgets |
| Notifications | `/api/notifications/` | Alertes et canaux |

---

## Auteur

**Adoum** — Etudiant en Informatique
**Projet de Fin d'Etudes (PFE) — 2026**
Entreprise d'accueil : **Sotifibre / SOTETEL — Tunisie**

---

## Licence

Projet academique — Usage interne Sotifibre.
Tous droits reserves © 2026.
