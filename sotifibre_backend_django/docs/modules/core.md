## **`/home/user/sotifibre/sotifibre_backend_django/apps/core/`**

```markdown
# ⚙️ Sotifibre Core - Documentation Technique

## Table des matières
1. [Introduction](#introduction)
2. [Structure du Core](#structure-du-core)
3. [Modèles de Base](#modèles-de-base)
4. [Mixins](#mixins)
5. [Utilitaires](#utilitaires)
6. [Permissions](#permissions)
7. [Validateurs](#validateurs)
8. [Constantes](#constantes)
9. [Réponses Standardisées](#réponses-standardisées)
10. [Exceptions](#exceptions)
11. [Pagination](#pagination)
12. [Middleware](#middleware)
13. [Configuration](#configuration)
14. [Bonnes Pratiques](#bonnes-pratiques)

---

## Introduction

Le module **Core** de Sotifibre constitue la fondation technique de la plateforme Business Intelligence. Il fournit l'ensemble des **composants réutilisables**, des **classes de base**, des **utilitaires** et des **fonctionnalités transversales** nécessaires au développement de toutes les applications BI.

### 📦 Ce que contient le Core
- ✅ **Modèles abstraits** - Classes de base pour tous les modèles
- ✅ **Mixins** - Fonctionnalités réutilisables (audit, cache, export...)
- ✅ **Utilitaires** - Fonctions helpers pour le formatage, calculs, etc.
- ✅ **Permissions** - Classes de permissions personnalisées
- ✅ **Validateurs** - Validation des données métier
- ✅ **Constantes** - Valeurs partagées entre applications
- ✅ **Réponses** - Format standardisé des réponses API
- ✅ **Exceptions** - Gestion d'erreurs personnalisée
- ✅ **Pagination** - Classes de pagination réutilisables
- ✅ **Middleware** - Composants de traitement des requêtes

### ❌ Ce que le Core ne contient PAS
- ❌ **Vues** - Les vues sont dans les applications métier
- ❌ **Sérializers** - Les sérializers sont dans les applications métier
- ❌ **URLs** - Les routes sont dans les applications métier
- ❌ **Modèles métier** - Seuls les modèles abstraits sont dans le core

---

## Structure du Core

```
apps/core/
├── __init__.py              # Configuration du module
├── admin.py                 # Interface d'administration Django
├── apps.py                  # Configuration de l'application Django
├── constants.py             # Constantes globales BI
├── exceptions.py            # Classes d'exceptions personnalisées
├── middleware.py            # Middlewares pour les requêtes
├── mixins.py                # Mixins pour modèles et vues
├── models.py                # Modèles de base abstraits
├── pagination.py            # Classes de pagination
├── permissions.py           # Classes de permissions
├── responses.py             # Fonctions de réponse standardisées
├── signals.py               # Signaux Django
├── utils.py                 # Fonctions utilitaires
├── validators.py            # Validateurs de données
```

---

## Modèles de Base

### 📌 `BaseModel`
Modèle abstrait de base avec UUID et timestamps.

```python
from apps.core.models import BaseModel

class MonModele(BaseModel):
    """Mon modèle métier"""
    nom = models.CharField(max_length=100)
    
    # Hérite automatiquement:
    # - id (UUID)
    # - created_at (DateTimeField)
    # - updated_at (DateTimeField)
```

### 📌 `SoftDeleteModel`
Modèle avec suppression logique.

```python
from apps.core.models import SoftDeleteModel

class Document(SoftDeleteModel):
    """Document avec suppression logique"""
    titre = models.CharField(max_length=200)
    
    # Hérite en plus:
    # - deleted_at (DateTimeField, null=True)
    
    # Utilisation:
    doc.delete()           # Suppression logique
    doc.hard_delete()      # Suppression physique
    doc.restore()          # Restauration
```

### 📌 `Config`
Configuration globale stockée en JSON.

```python
from apps.core.models import Config

# Créer une configuration
Config.objects.create(
    key='dashboard.default_theme',
    value={'primary': '#5470c6', 'layout': 'dark'},
    config_type='visualization',
    description='Thème par défaut des tableaux de bord'
)

# Récupérer une configuration
config = Config.objects.get(key='dashboard.default_theme')
theme = config.value  # Dictionnaire Python
```

---

## Mixins

### 📌 **Mixins pour Modèles**

#### `AuditMixin`
Ajoute le suivi des créateurs/modificateurs.

```python
from apps.core.mixins import AuditMixin

class Dashboard(AuditMixin, models.Model):
    name = models.CharField(max_length=100)
    # Hérite de created_by, updated_by, created_at, updated_at
    
    def save(self, request=None):
        # Passer request pour enregistrer l'utilisateur
        super().save(request=request)
```

#### `SoftDeleteMixin`
Suppression logique avec traçage utilisateur.

```python
from apps.core.mixins import SoftDeleteMixin

class DataSource(SoftDeleteMixin, models.Model):
    name = models.CharField(max_length=100)
    # Hérite de is_deleted, deleted_at, deleted_by
    
    # Utilisation:
    source.delete(user=request.user)  # Suppression logique
    source.restore()                   # Restauration
```

#### `VersionedMixin`
Versionnage automatique des données.

```python
from apps.core.mixins import VersionedMixin

class KPIDefinition(VersionedMixin, models.Model):
    name = models.CharField(max_length=100)
    formula = models.TextField()
    # Hérite de version, version_history
    
    # Chaque modification sauvegarde l'état précédent
    kpi.save()  # version incrémentée, historique mis à jour
    
    # Récupérer une version spécifique
    old_version = kpi.get_version(1)
```

#### `OrderableMixin`
Ordonnancement automatique.

```python
from apps.core.mixins import OrderableMixin

class Widget(OrderableMixin, models.Model):
    name = models.CharField(max_length=100)
    # Hérite de order, ordre automatique
    
    # Réordonner
    widget.move_up()    # Déplacer vers le haut
    widget.move_down()  # Déplacer vers le bas
```

#### `CacheableMixin`
Gestion du cache pour les modèles.

```python
from apps.core.mixins import CacheableMixin

class Report(CacheableMixin, models.Model):
    name = models.CharField(max_length=100)
    # Hérite de cache_prefix, cache_timeout
    
    report.save()        # Invalide automatiquement le cache
    report.delete()      # Invalide automatiquement le cache
```

### 📌 **Mixins pour Vues**

#### `AuditLogMixin`
Journalisation automatique des actions CRUD.

```python
from apps.core.mixins import AuditLogMixin
from rest_framework.viewsets import ModelViewSet

class DashboardViewSet(AuditLogMixin, ModelViewSet):
    # Les actions create/update/delete sont automatiquement journalisées
    pass
```

#### `OwnerFilterMixin`
Filtrage automatique par propriétaire.

```python
from apps.core.mixins import OwnerFilterMixin

class DocumentViewSet(OwnerFilterMixin, ModelViewSet):
    owner_field = 'created_by'  # Champ de propriété
    
    # Les admins voient tout
    # Les utilisateurs voient uniquement leurs documents
```

#### `SoftDeleteViewMixin`
Support de suppression logique dans les vues.

```python
from apps.core.mixins import SoftDeleteViewMixin

class DocumentViewSet(SoftDeleteViewMixin, ModelViewSet):
    # GET /documents/ - Exclut les supprimés
    # DELETE /documents/1/ - Suppression logique
    # POST /documents/1/restore/ - Restauration
```

#### `BulkActionViewMixin`
Actions groupées.

```python
from apps.core.mixins import BulkActionViewMixin

class UserViewSet(BulkActionViewMixin, ModelViewSet):
    bulk_update_fields = ['status', 'role']
    
    # Endpoints automatiques:
    # POST /users/bulk-delete/
    # POST /users/bulk-update/
```

#### `CachedQueryMixin`
Cache automatique des requêtes GET.

```python
from apps.core.mixins import CachedQueryMixin

class DataViewSet(CachedQueryMixin, ModelViewSet):
    cache_timeout = 300  # 5 minutes
    cache_key_prefix = 'data'
    
    # Les résultats GET sont automatiquement mis en cache
```

#### `ExportMixin`
Export vers CSV/Excel/JSON.

```python
from apps.core.mixins import ExportMixin

class SalesViewSet(ExportMixin, ModelViewSet):
    export_formats = ['csv', 'excel', 'json']
    
    # GET /sales/export?format=excel
```

#### `StatisticsMixin`
Endpoint de statistiques.

```python
from apps.core.mixins import StatisticsMixin

class DashboardViewSet(StatisticsMixin, ModelViewSet):
    def get_statistics(self, queryset):
        """Statistiques personnalisées"""
        return {
            'total': queryset.count(),
            'published': queryset.filter(is_published=True).count(),
            'avg_views': queryset.aggregate(Avg('views'))['views__avg']
        }
    
    # GET /dashboards/statistics/
```

#### `PerformanceMixin`
Monitoring des performances.

```python
from apps.core.mixins import PerformanceMixin

class SlowViewSet(PerformanceMixin, ModelViewSet):
    # Ajoute X-Query-Time-Ms dans les headers
    # Log les requêtes lentes (> 1s)
    pass
```

---

## Utilitaires

### 📌 **Formatage**

```python
from apps.core.utils import (
    format_number, format_percentage, format_bytes,
    format_duration, format_currency, truncate_string
)

# Nombres
format_number(1500000)                    # "1 500 000.00"
format_number(1500000, compact=True)      # "1.5M"
format_number(1500, decimals=0)           # "1 500"

# Pourcentages
format_percentage(15.5)                   # "15.5%"
format_percentage(15.5, include_sign=True) # "+15.5%"

# Tailles
format_bytes(1048576)                     # "1.0 MB"

# Durées
format_duration(3665)                     # "1.0h"

# Monnaies
format_currency(1250.5, '€')              # "1 250.50 €"

# Troncature
truncate_string("Long texte...", 10)      # "Long tex..."
```

### 📌 **Calculs**

```python
from apps.core.utils import (
    calculate_trend, calculate_percentage_change,
    safe_divide, calculate_statistics
)

# Tendance
trend = calculate_trend(current=120, previous=100)
# {
#     'value': 120,
#     'previous': 100,
#     'change': 20.0,
#     'direction': 'up',
#     'icon': '📈',
#     'percentage': '20.0%'
# }

# Division sécurisée
result = safe_divide(10, 0, default=0)    # 0

# Statistiques
stats = calculate_statistics(data, 'amount')
# {
#     'count': 100,
#     'sum': 125000,
#     'avg': 1250,
#     'min': 10,
#     'max': 10000,
#     'median': 850
# }
```

### 📌 **Dates**

```python
from apps.core.utils import get_date_range, get_date_ranges, parse_filter_params

# Plage de dates
start, end = get_date_range('month')       # Dernier mois
ranges = get_date_ranges()                 # Toutes les plages prédéfinies

# Paramètres de filtre
filters = parse_filter_params(request.query_params)
# Convertit date_from, date_to, date_range en filtres Django
```

### 📌 **Cache et Performance**

```python
from apps.core.utils import build_cache_key, rate_limit_check, Timer

# Clé de cache
key = build_cache_key('user', user_id, 'dashboard')

# Limitation de taux
if rate_limit_check('api:user:123', max_calls=10, period_seconds=60):
    # Dans les limites
    pass

# Timer de performance
with Timer("opération lourde") as timer:
    # Code à mesurer
    pass
print(f"Durée: {timer.duration_ms()}ms")
```

### 📌 **Graphiques**

```python
from apps.core.utils import get_color_palette, get_chart_config

# Palettes de couleurs
colors = get_color_palette('corporate')
# ['#003f5c', '#2c4c6e', '#58508d', ...]

# Configuration de graphique
config = get_chart_config('bar', {
    'categories': ['Jan', 'Fév', 'Mar'],
    'series': [{'name': 'Ventes', 'data': [100, 120, 150]}]
})
```

---

## Permissions

### 📌 **Permissions de Base**

```python
from apps.core.permissions import (
    IsSuperAdmin, IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin
)

class SensitiveViewSet(ModelViewSet):
    permission_classes = [IsSuperAdmin]  # Super admins uniquement

class AdminOnlyViewSet(ModelViewSet):
    permission_classes = [IsAdmin]        # Admins uniquement

class PublicReadViewSet(ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]  # Admins modifient, tous lisent
```

### 📌 **Permissions BI Spécifiques**

```python
from apps.core.permissions import (
    CanManageDataSources, CanViewDataSources,
    CanManageETL, CanViewETL,
    CanManageDashboards, CanViewDashboards,
    CanManageKPIs, CanViewKPIs,
    CanExportData, CanScheduleReports
)

class DataSourceViewSet(ModelViewSet):
    permission_classes = [CanManageDataSources]  # Gestion des sources
    
    def get_permissions(self):
        if self.action == 'list':
            return [CanViewDataSources()]  # Voir les sources
        return [CanManageDataSources()]    # Modifier les sources
```

### 📌 **Permissions par Rôle**

```python
from apps.core.permissions import (
    IsBIAnalyst, IsBIDeveloper, IsBIConsumer, HasFullBIAccess
)

class AnalyticsViewSet(ModelViewSet):
    permission_classes = [IsBIAnalyst | IsBIDeveloper]  # Analystes et devs
    
class ReadOnlyViewSet(ModelViewSet):
    permission_classes = [IsBIConsumer]  # Lecture seule
```

---

## Validateurs

### 📌 **SQL et Sécurité**

```python
from apps.core.validators import (
    validate_sql_query, validate_sql_identifier,
    validate_query_parameters
)

class QuerySerializer(serializers.Serializer):
    sql = serializers.CharField(validators=[validate_sql_query])
    params = serializers.JSONField(validators=[validate_query_parameters])
    table = serializers.CharField(validators=[validate_sql_identifier])
```

### 📌 **Sources de Données**

```python
from apps.core.validators import (
    validate_connection_string, validate_hostname, validate_port
)

class DataSourceSerializer(serializers.Serializer):
    connection = serializers.CharField(validators=[validate_connection_string])
    host = serializers.CharField(validators=[validate_hostname])
    port = serializers.IntegerField(validators=[validate_port])
```

### 📌 **BI Spécifiques**

```python
from apps.core.validators import (
    validate_chart_type, validate_chart_config,
    validate_dashboard_layout, validate_color_hex,
    validate_aggregation_function, validate_measure_formula
)

class ChartSerializer(serializers.Serializer):
    type = serializers.CharField(validators=[validate_chart_type])
    config = serializers.JSONField(validators=[validate_chart_config])
    color = serializers.CharField(validators=[validate_color_hex])

class DashboardSerializer(serializers.Serializer):
    layout = serializers.JSONField(validators=[validate_dashboard_layout])
    
class KPISerializer(serializers.Serializer):
    formula = serializers.CharField(validators=[validate_measure_formula])
    aggregation = serializers.CharField(validators=[validate_aggregation_function])
```

### 📌 **Planification**

```python
from apps.core.validators import (
    validate_cron_expression, validate_schedule_interval
)

class ReportSerializer(serializers.Serializer):
    schedule = serializers.CharField(validators=[validate_cron_expression])
    interval = serializers.CharField(validators=[validate_schedule_interval])
```

### 📌 **KPI**

```python
from apps.core.validators import (
    validate_kpi_threshold, validate_kpi_target
)

class KPISerializer(serializers.Serializer):
    target = serializers.FloatField(validators=[validate_kpi_target])
    threshold = serializers.JSONField(validators=[validate_kpi_threshold])
```

### 📌 **Génériques**

```python
from apps.core.validators import (
    validate_positive_integer, validate_percentage,
    validate_email_list, validate_domain_name, validate_url_safe
)

class SettingsSerializer(serializers.Serializer):
    max_items = serializers.IntegerField(validators=[validate_positive_integer])
    threshold = serializers.FloatField(validators=[validate_percentage])
    emails = serializers.ListField(validators=[validate_email_list])
    domain = serializers.CharField(validators=[validate_domain_name])
    slug = serializers.CharField(validators=[validate_url_safe])
```

---

## Constantes

```python
from apps.core.constants import (
    PLATFORM, CHART_TYPES, DATA_SOURCE_TYPES,
    ETL_STATUS, DASHBOARD_STATUS, BI_USER_ROLES
)

# Informations plateforme
print(PLATFORM['name'])        # "Sotifibre"
print(PLATFORM['version'])     # "1.0.0"

# Types de graphiques
chart_choices = CHART_TYPES.items()
# ('bar', '📊 Barres'), ('line', '📈 Ligne'), ...

# Types de sources
source_choices = DATA_SOURCE_TYPES.items()
# ('database', '🗄️ Base de données'), ...

# Statuts ETL
status_choices = ETL_STATUS.items()
# ('pending', '⏳ En attente'), ...

# Rôles BI
role_choices = BI_USER_ROLES.items()
# ('admin', '👑 Administrateur BI'), ...
```

---

## Réponses Standardisées

```python
from apps.core.responses import (
    success_response, error_response, created_response,
    bi_data_response, chart_data_response, dashboard_response
)

# Réponse de succès
return success_response(
    data={'id': 1, 'name': 'Dashboard'},
    message="Dashboard créé"
)
# {
#     "status": true,
#     "message": "Dashboard créé",
#     "data": {"id": 1, "name": "Dashboard"},
#     "timestamp": "2024-01-01T12:00:00Z"
# }

# Réponse d'erreur
return error_response(
    message="Source non trouvée",
    code="not_found",
    status_code=404
)
# {
#     "status": false,
#     "message": "Source non trouvée",
#     "code": "not_found",
#     "timestamp": "2024-01-01T12:00:00Z"
# }

# Réponse BI
return bi_data_response(
    data={'sales': 15000},
    metadata={'source': 'warehouse'}
)

# Réponse graphique
return chart_data_response(
    data={'categories': ['Q1', 'Q2'], 'values': [100, 150]},
    chart_config={'type': 'bar'}
)

# Réponse tableau de bord
return dashboard_response(
    dashboard_data={'id': 1, 'name': 'Sales'},
    layout={'widgets': [...]}
)
```

---

## Exceptions

```python
from apps.core.exceptions import (
    DataSourceNotFoundException,
    ConnectionFailedException,
    QueryExecutionException,
    DashboardNotFoundException,
    ETLPipelineException,
    ExportException
)

# Dans vos vues
try:
    data_source = DataSource.objects.get(id=source_id)
except DataSource.DoesNotExist:
    raise DataSourceNotFoundException(source_id=source_id)

try:
    result = execute_query(query)
except Exception as e:
    raise QueryExecutionException(query=query, message=str(e))
```

---

## Pagination

```python
from apps.core.pagination import StandardPagination, LargeResultsPagination

class SmallDatasetViewSet(ModelViewSet):
    pagination_class = StandardPagination  # 20 par page, max 100

class LargeDatasetViewSet(ModelViewSet):
    pagination_class = LargeResultsPagination  # 100 par page, max 1000
```

---

## Middleware

```python
# settings.py
MIDDLEWARE = [
    # ...
    'apps.core.middleware.RequestLoggingMiddleware',
    'apps.core.middleware.QueryPerformanceMiddleware',
    'apps.core.middleware.BIResponseMiddleware',
]
```

---

## Configuration

### 📌 **Cache**

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 📌 **Environnement**

```python
# .env
SOTIFIBRE_VERSION=1.0.0
SOTIFIBRE_ENVIRONMENT=production
CACHE_TTL=3600
MAX_EXPORT_ROWS=100000
```

---

## Bonnes Pratiques

### ✅ **À FAIRE**

1. **Toujours utiliser `BaseModel` pour les modèles**
```python
# Bon
class MyModel(BaseModel):
    pass

# Mauvais
class MyModel(models.Model):
    id = models.UUIDField(primary_key=True)
```

2. **Utiliser les mixins appropriés**
```python
# Bon
class DashboardViewSet(AuditLogMixin, CachedQueryMixin, ModelViewSet):
    pass

# Mauvais - Réimplémentation manuelle
class DashboardViewSet(ModelViewSet):
    def list(self, request):
        # Code de cache manuel
        pass
```

3. **Utiliser les réponses standardisées**
```python
# Bon
return success_response(data, "Succès")

# Mauvais
return Response({"success": True, "data": data})
```

4. **Valider les entrées utilisateur**
```python
# Bon
class QuerySerializer(serializers.Serializer):
    sql = serializers.CharField(validators=[validate_sql_query])

# Mauvais
class QuerySerializer(serializers.Serializer):
    sql = serializers.CharField()
```

### ❌ **À ÉVITER**

1. **Ne pas dupliquer le code du core** - Utilisez les composants fournis
2. **Ne pas contourner les middlewares** - Ils assurent sécurité et performance
3. **Ne pas ignorer les permissions** - Utilisez les classes de permission
4. **Ne pas stocker de configuration en dur** - Utilisez le modèle `Config`
5. **Ne pas mettre de logique métier dans le core** - Le core est pour les composants réutilisables

---

## Conclusion

Le module Core de Sotifibre fournit tous les composants réutilisables nécessaires pour construire des applications BI robustes. En utilisant ces composants, vous bénéficiez de :

- 🔒 **Sécurité** - Permissions et validation intégrées
- ⚡ **Performance** - Cache et optimisation
- 📊 **Standardisation** - Format unifié des réponses
- 🔧 **Productivité** - Composants prêts à l'emploi
- 📈 **Évolutivité** - Architecture modulaire

Pour toute question, contactez l'équipe Sotifibre Analytics.

---

**Version:** 3.0.0  
**Dernière mise à jour:** 21 Février 2026
```