## **`dataforge_backend/docs/modules/users.md`**

```markdown
# 👥 DataForge Users - Documentation Technique

## Table des matières
1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Modèles](#modèles)
4. [Authentification](#authentification)
5. [API REST](#api-rest)
6. [Permissions BI](#permissions-bi)
7. [Journalisation](#journalisation)
8. [Administration](#administration)
9. [Bonnes Pratiques](#bonnes-pratiques)
10. [Exemples](#exemples)

---

## Introduction

Le module **Users** de DataForge gère l'ensemble des aspects liés aux utilisateurs de la plateforme Business Intelligence. Il fournit un système complet de gestion des utilisateurs, rôles, équipes, permissions et journalisation des activités.

### 🎯 Objectifs
- 🔐 **Authentification sécurisée** - Support email/username, 2FA, verrouillage
- 👥 **Gestion des rôles BI** - Superadmin, Admin, Analyste, Développeur, Consommateur
- 🔑 **Permissions granulaires** - Contrôle fin des accès aux ressources BI
- 👥 **Gestion d'équipes** - Organisation des utilisateurs par équipe
- 📊 **Journalisation** - Traçabilité complète des actions utilisateur
- ⚙️ **Administration** - Interface d'administration riche

---

## Architecture

```
apps/users/
├── __init__.py              # Configuration du module
├── admin.py                 # Interface d'administration Django
├── apps.py                  # Configuration de l'application
├── authentication.py        # Backends d'authentification
├── filters.py               # Filtres personnalisés pour l'API
├── models.py                # Modèles de données
├── serializers.py           # Sérialiseurs pour l'API REST
├── signals.py               # Signaux Django
├── urls.py                  # Routes API
├── views.py                 # Vues API REST
└── management/
    └── commands/
        └── init_bi_roles.py # Commande d'initialisation
```

---

## Modèles

### 📌 **User - Utilisateur BI**

Modèle utilisateur étendu avec fonctionnalités BI.

```python
from apps.users.models import User

# Créer un utilisateur
user = User.objects.create_user(
    email="analyste@dataforge.tech",
    username="jdupont",
    password="secure123",
    first_name="Jean",
    last_name="Dupont",
    role="bi_analyst",
    department="Marketing"
)

# Propriétés de rôle
if user.can_manage_dashboards:
    # Créer un tableau de bord
    pass

if user.can_export_data:
    # Exporter des données
    pass
```

#### Champs Principaux

| Champ | Type | Description |
|-------|------|-------------|
| `email` | EmailField | Identifiant unique (login) |
| `username` | CharField | Nom d'utilisateur |
| `role` | ChoiceField | Rôle BI (superadmin, admin, bi_analyst, bi_developer, bi_consumer, viewer) |
| `status` | ChoiceField | Statut (active, inactive, suspended, locked) |
| `department` | CharField | Département |
| `job_title` | CharField | Poste |
| `employee_id` | CharField | Matricule |
| `api_access_enabled` | BooleanField | Accès API |
| `api_rate_limit` | IntegerField | Limite API (requêtes/heure) |
| `timezone` | CharField | Fuseau horaire |
| `theme` | ChoiceField | Thème (light/dark) |
| `two_factor_enabled` | BooleanField | 2FA activé |

#### Propriétés de Permissions BI

```python
# Sources de données
user.can_manage_data_sources   # Gérer les sources
user.can_view_data_sources     # Voir les sources

# ETL
user.can_manage_etl            # Gérer les pipelines ETL
user.can_view_etl              # Voir les pipelines ETL

# Visualisations
user.can_manage_visualizations # Gérer les visualisations
user.can_view_visualizations   # Voir les visualisations

# Tableaux de bord
user.can_manage_dashboards     # Gérer les dashboards
user.can_view_dashboards       # Voir les dashboards
user.can_create_dashboards     # Créer des dashboards
user.can_share_dashboards      # Partager des dashboards

# KPIs
user.can_manage_kpis           # Gérer les KPIs
user.can_view_kpis             # Voir les KPIs

# Rapports
user.can_export_data           # Exporter des données
user.can_schedule_reports      # Planifier des rapports
```

### 📌 **Team - Équipe**

Organisation des utilisateurs par équipe.

```python
from apps.users.models import Team

# Créer une équipe
team = Team.objects.create(
    name="Équipe BI Marketing",
    description="Équipe dédiée aux analyses marketing",
    team_lead=user
)

# Ajouter des membres
team.members.add(user1, user2, user3)

# Accéder aux membres
members = team.members.all()
```

### 📌 **Role - Rôle**

Rôles avec permissions associées.

```python
from apps.users.models import Role

# Créer un rôle personnalisé
role = Role.objects.create(
    name="bi_expert",
    description="Expert BI avec droits avancés",
    permissions=[
        "can_manage_data_sources",
        "can_manage_etl",
        "can_manage_dashboards",
        "can_export_data"
    ]
)

# Vérifier une permission
if role.has_permission("can_manage_dashboards"):
    # L'utilisateur peut gérer les dashboards
    pass
```

### 📌 **Permission - Permission**

Permissions individuelles.

```python
from apps.users.models import Permission

# Créer une permission
Permission.objects.create(
    code="can_manage_advanced_analytics",
    name="Gérer l'analytique avancée",
    description="Permet d'accéder aux fonctionnalités d'analytique avancée",
    category="analytics"
)
```

### 📌 **UserActivity - Activité Utilisateur**

Journal complet des actions.

```python
from apps.users.models import UserActivity

# Créer une activité
UserActivity.objects.create(
    user=user,
    action="dashboard_create",
    severity="medium",
    description="Création du dashboard 'Ventes Q1'",
    resource_type="dashboard",
    resource_id="123e4567-e89b-12d3-a456-426614174000",
    resource_name="Ventes Q1",
    ip_address="192.168.1.100",
    success=True
)
```

---

## Authentification

### 📌 **Backends d'authentification**

```python
# apps/users/authentication.py

# 1. EmailAuthBackend - Authentification par email ou username
# 2. APIAuthBackend - Vérification de l'accès API
# 3. TokenAuthBackend - Authentification par token
```

### 📌 **Configuration**

```python
# settings.py

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'apps.users.authentication.EmailAuthBackend',
    'apps.users.authentication.APIAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### 📌 **Connexion**

```python
# API - Connexion
POST /api/token/login/
{
    "username": "analyste@dataforge.tech",
    "password": "secure123"
}

# Réponse
{
    "status": true,
    "data": {
        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    }
}
```

---

## API REST

### 📌 **Endpoints Utilisateurs**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/users/` | Liste des utilisateurs |
| POST | `/api/users/` | Créer un utilisateur |
| GET | `/api/users/{id}/` | Détail utilisateur |
| PUT | `/api/users/{id}/` | Mettre à jour |
| DELETE | `/api/users/{id}/` | Supprimer |
| GET | `/api/users/me/` | Profil connecté |
| POST | `/api/users/change_password/` | Changer mot de passe |
| GET | `/api/users/stats/` | Statistiques globales |
| GET | `/api/users/activity_stats/` | Statistiques d'activité |
| GET | `/api/users/check_bi_permissions/` | Vérifier permissions BI |

### 📌 **Endpoints Équipes**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/teams/` | Liste des équipes |
| POST | `/api/teams/` | Créer une équipe |
| GET | `/api/teams/{id}/` | Détail équipe |
| PUT | `/api/teams/{id}/` | Mettre à jour |
| DELETE | `/api/teams/{id}/` | Supprimer |
| POST | `/api/teams/{id}/add_member/` | Ajouter membre |
| POST | `/api/teams/{id}/remove_member/` | Retirer membre |

### 📌 **Endpoints Rôles**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/roles/` | Liste des rôles |
| POST | `/api/roles/` | Créer un rôle |
| GET | `/api/roles/{id}/` | Détail rôle |
| PUT | `/api/roles/{id}/` | Mettre à jour |
| DELETE | `/api/roles/{id}/` | Supprimer |

### 📌 **Endpoints Permissions**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/permissions/` | Liste des permissions |
| GET | `/api/permissions/grouped/` | Permissions groupées |

### 📌 **Endpoints Activités**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/activities/` | Liste des activités |
| GET | `/api/activities/recent/` | Activités récentes (24h) |
| GET | `/api/activities/by_user/` | Activités par utilisateur |
| GET | `/api/activities/by_action/` | Activités par action |

---

## Permissions BI

### 📌 **Hiérarchie des Rôles**

```
👑 Super Administrateur
    └── ⚙️ Administrateur
        └── 💻 Développeur BI
            └── 📊 Analyste BI
                └── 📱 Consommateur BI
                    └── 👀 Observateur
```

### 📌 **Matrice des Permissions**

| Permission    | SuperAdmin | Admin | Dev BI | Analyste | Consommateur | Observateur |
|------------   |------------|-------|--------|----------|--------------|-------------|
| Gérer sources | ✓ | ✓ | ✓ | - | - | - |
| Voir sources  | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gérer ETL | ✓ | ✓ | ✓ | - | - | - |
| Voir ETL | ✓ | ✓ | ✓ | ✓ | - | - |
| Gérer dashboards | ✓ | ✓ | ✓ | ✓ | - | - |
| Créer dashboards | ✓ | ✓ | ✓ | ✓ | - | - |
| Voir dashboards | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Gérer KPIs | ✓ | ✓ | ✓ | ✓ | - | - |
| Voir KPIs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Exporter données | ✓ | ✓ | ✓ | ✓ | - | - |
| Planifier rapports | ✓ | ✓ | ✓ | ✓ | - | - |

### 📌 **Utilisation dans les Vues**

```python
from apps.core.permissions import (
    CanManageDataSources, CanViewDataSources,
    CanManageDashboards, CanViewDashboards
)
from rest_framework.viewsets import ModelViewSet

class DashboardViewSet(ModelViewSet):
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [CanViewDashboards]
        else:
            permission_classes = [CanManageDashboards]
        return [permission() for permission in permission_classes]
```

---

## Journalisation

### 📌 **Types d'activités**

```python
# Authentification
'login', 'logout'

# CRUD
'create', 'update', 'delete', 'view'

# BI Spécifiques
'dashboard_create', 'dashboard_share'
'data_source_test', 'etl_run'
'export', 'import', 'share', 'schedule'
```

### 📌 **Niveaux de sévérité**

```python
'low'      # Actions normales (login, view)
'medium'   # Modifications (update, create)
'high'     # Actions importantes (delete, export)
'critical' # Actions critiques (user deletion, role change)
```

### 📌 **Exemple de journalisation**

```python
from apps.users.models import UserActivity

def perform_create(self, serializer):
    instance = serializer.save()
    
    UserActivity.objects.create(
        user=self.request.user,
        action='create',
        severity='medium',
        description=f"Dashboard '{instance.name}' créé",
        resource_type='dashboard',
        resource_id=str(instance.id),
        resource_name=instance.name,
        ip_address=self.request.META.get('REMOTE_ADDR'),
        success=True
    )
    
    return instance
```

---

## Administration

### 📌 **Interface Admin**

L'interface d'administration Django offre des fonctionnalités avancées :

#### Actions groupées
- ✅ Activer/Désactiver utilisateurs
- 🚫 Suspendre utilisateurs
- 🔓 Déverrouiller comptes
- ✓ Activer/Désactiver API
- 📤 Exporter sélection

#### Filtres disponibles
- Rôle BI (superadmin, admin, analyste...)
- Statut (actif, inactif, suspendu, verrouillé)
- Département
- Accès API
- 2FA
- Date d'inscription

#### Recherche
- Email
- Nom d'utilisateur
- Prénom/Nom
- Matricule

### 📌 **Commandes d'initialisation**

```bash
# Créer un superutilisateur
python manage.py createsuperuser

# Initialiser les rôles BI par défaut
python manage.py init_bi_roles

# Nettoyer les activités anciennes (30 jours)
python manage.py cleanup_activities --days=30

# Vérifier l'intégrité des permissions
python manage.py check_permissions
```

---

## Bonnes Pratiques

### ✅ **À FAIRE**

1. **Utiliser les permissions intégrées**
```python
# Bon
if user.can_manage_dashboards:
    # Créer dashboard

# Mauvais
if user.role in ['admin', 'superadmin']:
    # Créer dashboard
```

2. **Journaliser les actions importantes**
```python
# Bon
UserActivity.objects.create(
    user=request.user,
    action='export',
    description=f"Export de {count} lignes",
    success=True
)
```

3. **Vérifier l'accès API**
```python
# Bon
if not request.user.api_access_enabled:
    return error_response("Accès API désactivé")
```

4. **Utiliser les filtres de sécurité**
```python
# Bon
if user.is_account_locked:
    return error_response("Compte verrouillé")
```

### ❌ **À ÉVITER**

1. **Ne pas stocker de mots de passe en clair**
2. **Ne pas ignorer les tentatives de connexion échouées**
3. **Ne pas donner trop de permissions aux rôles par défaut**
4. **Ne pas désactiver la journalisation en production**
5. **Ne pas utiliser de comptes partagés**

---

## Exemples

### 📌 **Créer un analyste BI**

```python
from apps.users.models import User

analyst = User.objects.create_user(
    email="analyste@company.com",
    username="analyst1",
    password="secure123",
    first_name="Marie",
    last_name="Martin",
    role="bi_analyst",
    department="Sales",
    job_title="Business Analyst",
    api_access_enabled=True,
    api_rate_limit=500
)
```

### 📌 **Créer une équipe BI**

```python
from apps.users.models import Team, User

# Récupérer le chef d'équipe
team_lead = User.objects.get(email="lead@company.com")

# Créer l'équipe
team = Team.objects.create(
    name="BI Sales Team",
    description="Équipe BI dédiée aux ventes",
    team_lead=team_lead
)

# Ajouter des membres
members = User.objects.filter(role="bi_analyst", department="Sales")
team.members.add(*members)
```

### 📌 **Vérifier les permissions avant action**

```python
from apps.core.responses import forbidden_response

def create_dashboard(self, request):
    if not request.user.can_create_dashboards:
        return forbidden_response(
            "Permission de création de dashboard requise",
            required_permission="can_create_dashboards"
        )
    
    # Créer le dashboard
    dashboard = Dashboard.objects.create(
        name=request.data['name'],
        created_by=request.user
    )
    
    # Journaliser
    UserActivity.objects.create(
        user=request.user,
        action="dashboard_create",
        description=f"Dashboard '{dashboard.name}' créé",
        resource_type="dashboard",
        resource_id=str(dashboard.id),
        success=True
    )
    
    return success_response(dashboard.data)
```

### 📌 **Filtrer les utilisateurs par permission**

```python
from django.db.models import Q

# Utilisateurs pouvant gérer les dashboards
dashboard_managers = User.objects.filter(
    Q(role='superadmin') |
    Q(role='admin') |
    Q(role='bi_developer') |
    Q(role='bi_analyst')
)

# Utilisateurs actifs avec accès API
active_api_users = User.objects.filter(
    status='active',
    api_access_enabled=True
)
```

### 📌 **Analyser les activités utilisateur**

```python
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

# Activités des 7 derniers jours
last_week = timezone.now() - timedelta(days=7)
activities = UserActivity.objects.filter(
    created_at__gte=last_week
)

# Top 10 des utilisateurs les plus actifs
top_users = activities.values('user__email').annotate(
    count=Count('id')
).order_by('-count')[:10]

# Actions les plus fréquentes
top_actions = activities.values('action').annotate(
    count=Count('id')
).order_by('-count')

# Taux de succès par action
success_rate = activities.values('action').annotate(
    total=Count('id'),
    success=Count('id', filter=Q(success=True))
)
```

---

## Sécurité

### 🔒 **Recommandations**

1. **Activer 2FA pour les comptes sensibles**
```python
user.two_factor_enabled = True
user.save()
```

2. **Limiter les tentatives de connexion**
```python
# Automatiquement géré par le modèle
user.increment_failed_attempts()  # Après 5 échecs, verrouillage 30 min
```

3. **Désactiver les comptes inactifs**
```python
from django.utils import timezone
from datetime import timedelta

inactive_since = timezone.now() - timedelta(days=90)
inactive_users = User.objects.filter(
    last_activity_at__lt=inactive_since,
    status='active'
).update(status='inactive', is_active=False)
```

4. **Auditer régulièrement**
```python
# Utilisateurs avec rôles sensibles
admin_users = User.objects.filter(role__in=['superadmin', 'admin'])

# Activités suspectes
suspicious = UserActivity.objects.filter(
    severity='critical',
    created_at__gte=timezone.now() - timedelta(days=7)
)
```

---

## Dépannage

### 🐛 **Problèmes courants**

| Problème | Solution |
|----------|----------|
| Authentification échouée | Vérifier email et mot de passe, compte non verrouillé |
| Permission refusée | Vérifier le rôle et les permissions de l'utilisateur |
| API inaccessible | Vérifier `api_access_enabled` et le token |
| Activités non journalisées | Vérifier que les signaux sont bien connectés |
| Compte verrouillé | Attendre 30 min ou utiliser `reset_failed_attempts()` |

---

## Conclusion

Le module Users de DataForge offre une base solide pour la gestion des utilisateurs BI avec :

- 🔐 **Sécurité renforcée** - 2FA, verrouillage, journalisation
- 👥 **Gestion avancée** - Rôles, équipes, permissions granulaires
- 📊 **API complète** - Endpoints REST pour toutes les fonctionnalités
- 📝 **Traçabilité** - Journalisation complète des actions
- ⚙️ **Administration** - Interface riche avec actions groupées

---

**Version:** 1.0.0  
**Dernière mise à jour:** 21 Mars 2026  
**Mainteneur:** DataForge Analytics
```