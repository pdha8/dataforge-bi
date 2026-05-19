# DataForge BI — Frontend

Interface web de la plateforme **DataForge BI** (Vue 3 + TypeScript), une plateforme BI open source.

🌐 **Démo en production** : [dataforge-app.onrender.com](https://dataforge-app.onrender.com)

---

## Aperçu

Single-Page Application (SPA) qui consomme l'API Django backend pour la gestion complète d'une plateforme BI : sources de données, ETL, data warehouse, visualisations, KPI, rapports, analyses ML.

22 vues couvrant l'intégralité des fonctionnalités, design system maison en CSS natif (tokens), responsive mobile, mode hash routing (robuste face au refresh sur les routes profondes).

---

## Stack technique

| Outil | Version | Rôle |
|---|---|---|
| **Vue 3** | 3.5 | Framework UI (Composition API + `<script setup>`) |
| **TypeScript** | 6.0 | Typage statique strict |
| **Vite** | 8.0 | Bundler + dev server |
| **Vue Router** | 4.6 | Routing SPA (hash mode) |
| **Pinia** | 3.0 | Gestion d'état centralisée |
| **Axios** | 1.16 | Client HTTP avec intercepteurs JWT |
| **Chart.js + vue-chartjs** | 4.5 / 5.3 | Graphiques (Bar/Line/Pie/Doughnut/Scatter) |
| **Headless UI Vue** | 1.7 | Modales et menus accessibles |
| **Lucide Vue Next** | 1.0 | Icônes (~1400 SVG) |

---

## Démarrage rapide

### Prérequis
- Node.js 20 LTS ou supérieur
- npm 10+

### Installation
```bash
npm install
```

### Développement local
```bash
npm run dev
```
Le serveur démarre sur `http://localhost:5173`. Par défaut, le frontend tape `http://localhost:8000` pour l'API backend (Django runserver).

### Pointer vers la prod Render
Créer un fichier `.env.local` :
```env
VITE_API_URL=https://dataforge-api.onrender.com
```
Puis relancer `npm run dev`.

### Build de production
```bash
npm run build           # produit dist/
npm run preview         # sert dist/ sur :4173 (par défaut)
```

### Type-check sans build
```bash
npm run type-check
```

---

## Comptes de démonstration (prod)

| Rôle | Email | Mot de passe |
|---|---|---|
| Superadmin | admin@dataforge.tech | `DataForge@2026!` |
| Développeur BI | dev.bi@dataforge.tech | `DataForge@2026!` |
| Analyste BI | analyste@dataforge.tech | `DataForge@2026!` |
| Direction | direction@dataforge.tech | `DataForge@2026!` |

---

## Arborescence

```
dataforge_frontend/
├── src/
│   ├── api/                # Instance axios + interceptor JWT refresh
│   ├── components/
│   │   ├── header/         # AppHeader (notifs, user menu)
│   │   ├── sidebar/        # AppSidebar (drawer mobile)
│   │   └── ui/             # Composants utilitaires partagés
│   ├── layouts/
│   │   └── AppLayout.vue   # Sidebar + Header + <router-view>
│   ├── router/
│   │   └── index.ts        # Routes + guards (auth, role, permission)
│   ├── stores/
│   │   └── auth.ts         # Pinia store JWT + rôle + permissions
│   ├── views/              # 22 vues
│   │   ├── auth/           # LoginView
│   │   ├── dashboard/      # DashboardView (page d'accueil)
│   │   ├── sources/        # Sources, Connections, Files, Monitoring, Queries, Power Queries
│   │   ├── pipelines/      # PipelinesView (ETL)
│   │   ├── warehouse/      # WarehouseView
│   │   ├── star-schema/    # StarSchemaView (faits, dimensions, galaxies)
│   │   ├── visualizations/ # Widgets
│   │   ├── dashboards/     # Tableaux de bord composés
│   │   ├── kpis/           # Indicateurs
│   │   ├── reports/        # Rapports périodiques
│   │   ├── executions/     # Historique ETL
│   │   ├── notifications/  # Centre de notifications
│   │   ├── favorites/      # Éléments favoris
│   │   ├── ml-analytics/   # Modèles ML, forecasts, anomalies
│   │   ├── admin/          # Administration (users, rôles, équipes)
│   │   └── profile/        # Profil utilisateur
│   ├── App.vue
│   └── main.ts
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## Choix techniques notables

### Routing en mode hash
Le router utilise `createWebHashHistory()` au lieu de l'history-mode classique. Les URL produites sont du type `/#/dashboard` et ne sont jamais transmises au serveur — un refresh sur n'importe quelle route renvoie toujours `index.html` côté Render Static Site, sans configuration de réécriture.

### Auth JWT avec refresh automatique
L'instance axios (`src/api/axios.ts`) intercepte les réponses 401/403 et tente automatiquement un refresh via `/api/auth/jwt/refresh/`. Si le refresh échoue, l'utilisateur est redirigé vers `/login` et l'état Pinia est purgé.

### Guards de navigation
Les routes protégées déclarent leurs prérequis dans le `meta` :
- `requiresAuth: true` — utilisateur connecté requis
- `requiresGuest: true` — pour `/login`, redirige vers `/dashboard` si déjà connecté
- `requiresRole: ['superadmin', 'admin']` — restriction par rôle
- `requiresPermission: 'canManageETL'` — permission granulaire

### Design system
Tous les tokens (couleurs, espacements, rayons, ombres, fontes) sont déclarés en variables CSS dans `src/assets/`. Pas de Tailwind, pas de Bootstrap — uniquement du CSS écrit à la main, ce qui garantit la cohérence visuelle et facilite l'ajout d'un thème sombre.

### Responsive
- Sidebar → drawer en dessous de 768 px (overlay sombre, fermeture au tap extérieur)
- Tableaux → scroll horizontal (`overflow-x: auto`)
- Grilles de KPI → colonne unique
- Formulaires → pleine largeur, hauteur des inputs ≥ 40 px (cible tactile)

---

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL du backend Django |

---

## Tests

Les tests E2E sont gérés via **TestSprite MCP** au niveau du projet global (dossier `../testsprite_tests/` non versionné). Une suite Playwright autonome existe également dans `../tests/e2e/`.

**Score E2E actuel : 28 / 30 passants (93,3 %)**. Détail dans le fichier `../TESTING_REPORT.md`.

---

## Déploiement

Hébergé en **Static Site** sur Render :
- Build Command : `npm install && npm run build`
- Publish Directory : `dist`
- Variable : `VITE_API_URL=https://dataforge-api.onrender.com`

Le push sur `master` déclenche le redéploiement automatique (environ 2 minutes).

---

*DataForge BI — Open Source — Djafar Ahmat Mahamat Moussa, 2026*
