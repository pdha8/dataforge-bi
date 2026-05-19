# 📊 DataForge BI Platform — Documentation backend

Bienvenue dans la documentation technique du backend Django de la plateforme **Integrated BI**.

Pour une présentation générale + démarrage rapide, voir le [`README.md`](../README.md) à la racine de `dataforge_backend/`.

---

## 📂 Architecture

- [Vue d'ensemble](architecture/overview.md) — couches applicatives, dépendances
- [Flux de données](architecture/data-flow.md) — du source à la visualisation
- [Sécurité](architecture/security.md) — JWT, permissions, RBAC

## 🔌 API

- [Référence des endpoints](api/endpoints.md) — la liste exhaustive est aussi générée automatiquement par drf-spectacular (`/api/schema/swagger-ui/`)
- [Authentification](api/authentication.md) — flux JWT (access + refresh)
- [Format d'erreur standard](api/errors.md)

## 🎯 Modules

- [Core](modules/core.md) — réponses standardisées, helpers, signaux
- [Users](modules/users.md) — utilisateurs, rôles, équipes, permissions
- [Data Sources](modules/data_sources.md) — connexions, queries, fichiers
- [ETL Engine](modules/etl_engine.md) — pipelines, transformations, exécutions
- [Data Warehouse](modules/data_warehouse.md) — schémas, faits, dimensions
- [Star Schema](modules/star_schema.md) — modélisation dimensionnelle avancée
- [Visualisations](modules/visualizations.md) — dashboards, widgets, KPI, rapports

## 🛠️ Développement

- [Installation et configuration](development/setup.md)
- [Guide de contribution](development/contributing.md)
- [Tests](development/testing.md)

---

**Documentation API live** : [/api/docs/](https://dataforge-api.onrender.com/api/docs/) (Swagger UI) · [/api/redoc/](https://dataforge-api.onrender.com/api/redoc/) (ReDoc)
