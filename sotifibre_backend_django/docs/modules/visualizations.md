```markdown
# 📊 Visualizations Module Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Models](#core-models)
4. [Dashboard Management](#dashboard-management)
5. [Widgets](#widgets)
6. [KPIs (Key Performance Indicators)](#kpis-key-performance-indicators)
7. [Reports](#reports)
8. [Favorites](#favorites)
9. [Activities & Audit](#activities--audit)
10. [API Endpoints](#api-endpoints)
11. [Usage Examples](#usage-examples)
12. [Best Practices](#best-practices)
13. [Performance Optimization](#performance-optimization)
14. [Troubleshooting](#troubleshooting)

---

## Overview

Le module **Visualizations** est le cœur de la présentation et de l'analyse BI de la plateforme Sotifibre. Il permet de créer, gérer et partager des tableaux de bord interactifs, des indicateurs de performance (KPIs) et des rapports automatisés.

### Fonctionnalités Clés

| Fonctionnalité | Description |
|----------------|-------------|
| **Tableaux de bord** | Création de dashboards interactifs avec layout drag-and-drop |
| **Widgets** | Graphiques, métriques, tableaux, textes, iframes, etc. |
| **KPIs** | Indicateurs de performance avec seuils, tendances et statuts |
| **Rapports** | Génération et planification de rapports multi-formats |
| **Favoris** | Marquage des dashboards et KPIs favoris |
| **Journalisation** | Traçage complet des activités utilisateurs |
| **Export** | Export en PNG, SVG, PDF, CSV, Excel, JSON, HTML |

### Types de Visualisations Supportées

| Type | Description |
|------|-------------|
| **Barres** | Comparaison de catégories |
| **Ligne** | Évolution temporelle |
| **Camembert** | Répartition en pourcentage |
| **Aire** | Volumes cumulés |
| **Nuage de points** | Corrélations |
| **Heatmap** | Matrices de densité |
| **Jauge** | Indicateurs de performance |
| **Radar** | Comparaison multi-critères |
| **Treemap** | Hiérarchies et proportions |
| **Sankey** | Flux et transitions |
| **Sunburst** | Hiérarchies radiales |
| **Waterfall** | Variations cumulées |
| **Boîte à moustaches** | Distribution statistique |
| **Histogramme** | Distribution de fréquences |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Visualizations Layer                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Dashboard (Tableau de bord)                    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │ │
│  │  │   Widget    │  │    KPI      │  │   Report    │  │  Favorite │ │ │
│  │  │ (Graphique) │  │ (Indicateur)│  │  (Rapport)  │  │  (Favori) │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    VisualizationActivity (Journal)                  │    │
│  │         Traçage des vues, exports, partages, éditions               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Data Sources Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │ Star Schema │  │Data Warehouse│ │   ETL Engine │  │   Data Sources │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Models

### 1. Dashboard
Tableau de bord principal regroupant widgets et KPIs.

```python
class Dashboard(BaseModel):
    # Identité
    name = models.CharField(max_length=200)          # Nom du dashboard
    slug = models.SlugField(unique=True)             # Identifiant URL
    description = models.TextField(blank=True)       # Description
    dashboard_type = models.CharField(max_length=20) # Type: analytical, operational, executive
    status = models.CharField(max_length=20)         # Statut: draft, published, archived
    
    # Layout
    layout = models.JSONField()                      # Configuration GridStack
    theme = models.CharField(max_length=20)          # Thème: light, dark, corporate
    custom_css = models.TextField(blank=True)        # CSS personnalisé
    custom_js = models.TextField(blank=True)         # JavaScript personnalisé
    
    # Configuration
    global_filters = models.JSONField()              # Filtres globaux
    refresh_frequency = models.CharField()           # Fréquence de rafraîchissement
    auto_refresh = models.BooleanField(default=False)# Auto rafraîchissement
    
    # Accès
    access_level = models.CharField()                # private, team, organization, public
    owner = models.ForeignKey(User)                  # Propriétaire
    team = models.ForeignKey(Team)                   # Équipe
    allowed_users = models.ManyToManyField(User)     # Utilisateurs autorisés
    
    # Statistiques
    view_count = models.IntegerField(default=0)      # Nombre de vues
    favorite_count = models.IntegerField(default=0)  # Nombre de favoris
    avg_load_time_ms = models.FloatField(default=0)  # Temps de chargement moyen
```

**Exemple de création :**
```python
dashboard = Dashboard.objects.create(
    name="Dashboard Commercial",
    slug="commercial-dashboard",
    description="Suivi des performances commerciales",
    dashboard_type="analytical",
    status="published",
    theme="light",
    layout={
        "grid": [
            {"x": 0, "y": 0, "w": 6, "h": 4, "widget_id": "widget_1"},
            {"x": 6, "y": 0, "w": 6, "h": 4, "widget_id": "widget_2"}
        ]
    },
    refresh_frequency="hourly",
    access_level="team",
    owner=admin_user,
    team=team_ventes
)
```

### 2. Widget
Élément individuel d'un tableau de bord.

```python
class Widget(BaseModel):
    # Identité
    name = models.CharField(max_length=200)          # Nom du widget
    description = models.TextField(blank=True)       # Description
    widget_type = models.CharField(max_length=20)    # Type: chart, metric, table, text
    
    # Parent
    dashboard = models.ForeignKey(Dashboard)         # Dashboard parent
    
    # Données
    dimensional_schema = models.ForeignKey(DimensionalSchema)  # Source de données
    config = models.JSONField()                      # Configuration du widget
    filters = models.JSONField()                     # Filtres spécifiques
    
    # Position
    position = models.JSONField()                    # x, y, w, h dans la grille
    
    # Style
    style = models.JSONField(blank=True)             # Style CSS personnalisé
    
    # Interactivité
    drilldown_enabled = models.BooleanField(default=False)
    drilldown_config = models.JSONField(blank=True)
    
    # Cache
    cache_enabled = models.BooleanField(default=True)
    cache_ttl_seconds = models.IntegerField(default=300)
    cached_data = models.JSONField(blank=True)
    
    # Métadonnées
    is_enabled = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Statistiques
    render_count = models.IntegerField(default=0)
    avg_render_time_ms = models.FloatField(default=0)
```

**Exemple de création :**
```python
widget = Widget.objects.create(
    name="Évolution des Ventes",
    description="Graphique d'évolution des ventes mensuelles",
    widget_type="chart",
    dashboard=dashboard,
    dimensional_schema=schema_ventes,
    config={
        "type": "line",
        "x_axis": "date",
        "y_axis": "montant",
        "title": "Ventes mensuelles"
    },
    position={"x": 0, "y": 0, "w": 12, "h": 6},
    cache_enabled=True,
    cache_ttl_seconds=600,
    is_enabled=True
)
```

### 3. KPI (Key Performance Indicator)
Indicateur de performance clé.

```python
class KPI(BaseModel):
    # Identité
    name = models.CharField(max_length=200)          # Nom du KPI
    description = models.TextField(blank=True)       # Description
    kpi_type = models.CharField(max_length=20)       # Type: number, percentage, currency
    
    # Source
    dimensional_schema = models.ForeignKey(DimensionalSchema)
    measure = models.ForeignKey(Measure, null=True)
    formula = models.TextField(blank=True)           # Formule personnalisée
    aggregation = models.CharField(max_length=20)    # sum, avg, count, min, max
    
    # Seuils
    target_value = models.FloatField(null=True)      # Valeur cible
    warning_threshold = models.FloatField(null=True) # Seuil d'alerte
    critical_threshold = models.FloatField(null=True)# Seuil critique
    
    # Formatage
    format_string = models.CharField(max_length=50)  # Format d'affichage
    unit = models.CharField(max_length=50)           # Unité
    decimal_places = models.IntegerField(default=2)  # Décimales
    
    # Tendances
    track_trend = models.BooleanField(default=True)  # Suivi de tendance
    trend_period = models.CharField()                # Période de comparaison
    
    # Valeurs calculées
    current_value = models.FloatField(null=True)     # Valeur actuelle
    previous_value = models.FloatField(null=True)    # Valeur précédente
    trend_percentage = models.FloatField(null=True)  # Pourcentage de tendance
```

**Exemple de création :**
```python
kpi = KPI.objects.create(
    name="Chiffre d'Affaires",
    description="CA total du mois en cours",
    kpi_type="currency",
    dimensional_schema=schema_ventes,
    measure=measure_ca,
    aggregation="sum",
    target_value=1000000,
    warning_threshold=800000,
    critical_threshold=500000,
    format_string="€#,##0.00",
    unit="EUR",
    decimal_places=2,
    track_trend=True,
    trend_period="previous_month"
)

# Calculer la valeur
result = kpi.calculate()
print(f"Valeur: {result['value']} €")
print(f"Tendance: {result['trend_percentage']}%")
print(f"Statut: {kpi.get_status()}")  # success, warning, critical
```

### 4. Report
Rapport programmé.

```python
class Report(BaseModel):
    # Identité
    name = models.CharField(max_length=200)          # Nom du rapport
    description = models.TextField(blank=True)       # Description
    
    # Source
    dashboard = models.ForeignKey(Dashboard)         # Dashboard source
    
    # Configuration
    format = models.CharField(max_length=20)         # pdf, csv, excel, json, html
    schedule = models.CharField(max_length=100)      # Expression CRON
    recipients = models.JSONField()                  # Liste des emails
    
    # Options
    filters = models.JSONField(blank=True)           # Filtres à appliquer
    include_metadata = models.BooleanField(default=True)
    include_filters = models.BooleanField(default=True)
    page_size = models.CharField(max_length=20)      # A4, Letter, etc.
    orientation = models.CharField(max_length=10)    # portrait, landscape
    
    # Génération
    last_generated = models.DateTimeField(null=True)
    generation_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
```

**Exemple de création :**
```python
report = Report.objects.create(
    name="Rapport Ventes Mensuel",
    description="Rapport mensuel des ventes",
    dashboard=dashboard,
    format="pdf",
    schedule="0 9 1 * *",  # Tous les 1er du mois à 9h
    recipients=["direction@entreprise.com", "finance@entreprise.com"],
    filters={"date_range": "last_month"},
    include_metadata=True,
    orientation="landscape"
)

# Générer manuellement
result = report.generate(user=admin_user)
```

### 5. Favorite
Favoris utilisateur.

```python
class Favorite(BaseModel):
    user = models.ForeignKey(User)                   # Utilisateur
    dashboard = models.ForeignKey(Dashboard)         # Dashboard favori
    kpi = models.ForeignKey(KPI)                     # KPI favori
    report = models.ForeignKey(Report)               # Rapport favori
    order = models.IntegerField(default=0)           # Ordre d'affichage
    notes = models.TextField(blank=True)             # Notes personnelles
```

### 6. VisualizationActivity
Journal des activités.

```python
class VisualizationActivity(BaseModel):
    ACTIVITY_TYPES = [
        ('view', '👁️ Vue'),
        ('export', '📤 Export'),
        ('share', '🔗 Partage'),
        ('edit', '✏️ Édition'),
        ('favorite', '⭐ Favori'),
        ('comment', '💬 Commentaire'),
    ]
    
    user = models.ForeignKey(User)                   # Utilisateur
    dashboard = models.ForeignKey(Dashboard)         # Dashboard concerné
    widget = models.ForeignKey(Widget)               # Widget concerné
    activity_type = models.CharField(max_length=20)  # Type d'activité
    description = models.TextField()                 # Description
    metadata = models.JSONField(blank=True)          # Métadonnées
    ip_address = models.GenericIPAddressField()      # Adresse IP
    user_agent = models.TextField()                  # User Agent
```

---

## Dashboard Management

### Types de Dashboards

| Type | Icône | Description | Utilisation |
|------|-------|-------------|-------------|
| **Analytique** | 📊 | Analyse approfondie des données | Exploration, découverte |
| **Opérationnel** | ⚙️ | Suivi quotidien des opérations | Monitoring temps réel |
| **Exécutif** | 👔 | Vue stratégique pour la direction | KPIs, objectifs |
| **Stratégique** | 🎯 | Planification long terme | Tendances, prévisions |
| **Tactique** | ⚡ | Décisions opérationnelles | Actions à court terme |
| **Personnalisé** | 🎨 | Configuration libre | Besoins spécifiques |

### Niveaux d'Accès

| Niveau | Description | Visibilité |
|--------|-------------|------------|
| **Privé** | 🔒 Seul le propriétaire | Propriétaire uniquement |
| **Équipe** | 👥 Membres de l'équipe | Toute l'équipe |
| **Organisation** | 🏢 Tous les utilisateurs | Toute l'organisation |
| **Public** | 🌍 Tout le monde | Public (lecture seule) |
| **Public modifiable** | 🌍✏️ Tout le monde | Public (modifiable) |

### Layout et Grille

Le layout utilise GridStack pour un positionnement flexible :

```python
layout = {
    "grid": [
        {
            "x": 0, "y": 0, "w": 6, "h": 4,  # Position et taille
            "widget_id": "uuid_widget_1",     # ID du widget
            "min_w": 2, "min_h": 2,           # Taille minimale
            "max_w": 12, "max_h": 8           # Taille maximale
        }
    ],
    "cols": 12,          # Nombre de colonnes
    "row_height": 50,    # Hauteur de ligne en pixels
    "margin": 10         # Marge entre widgets
}
```

### Thèmes Disponibles

| Thème | Couleur primaire | Fond | Utilisation |
|-------|------------------|------|-------------|
| **Light** | #667eea | Blanc | Défaut, jour |
| **Dark** | #764ba2 | Noir | Nuit, écrans OLED |
| **Corporate** | #003f5c | Blanc cassé | Entreprise |
| **Scientific** | #2c4c6e | Gris clair | Recherche |
| **Vibrant** | #ff6b6b | Blanc | Présentations |
| **Pastel** | #88b0dc | Blanc cassé | Rapports |

---

## Widgets

### Types de Widgets

#### 1. Chart (Graphique)
```python
widget = Widget.objects.create(
    widget_type="chart",
    config={
        "type": "bar",                    # Type de graphique
        "title": "Ventes par produit",    # Titre
        "x_axis": {"name": "Produit"},    # Axe X
        "y_axis": {"name": "Montant"},    # Axe Y
        "legend": {"show": True},         # Légende
        "tooltip": {"show": True},        # Info-bulle
        "colors": ["#5470c6", "#fac858"]  # Couleurs
    }
)
```

#### 2. Metric (Métrique)
```python
widget = Widget.objects.create(
    widget_type="metric",
    config={
        "value": 125000,
        "format": "€#,##0.00",
        "unit": "EUR",
        "trend": 15.5,
        "trend_direction": "up",
        "comparison": "previous_month"
    }
)
```

#### 3. Table (Tableau)
```python
widget = Widget.objects.create(
    widget_type="table",
    config={
        "columns": [
            {"name": "produit", "label": "Produit"},
            {"name": "ventes", "label": "Ventes", "format": "€#,##0"}
        ],
        "sortable": True,
        "searchable": True,
        "pagination": {"page_size": 10}
    }
)
```

#### 4. Text (Texte)
```python
widget = Widget.objects.create(
    widget_type="text",
    config={
        "content": "<h3>Résumé des ventes</h3><p>Le mois dernier...</p>",
        "markdown": True
    }
)
```

### Cache Configuration

```python
# Activer le cache
widget.cache_enabled = True
widget.cache_ttl_seconds = 600  # 10 minutes

# Vider le cache manuellement
widget.clear_cache()

# Cache automatique
def get_widget_data(widget):
    if widget.cache_enabled and widget.cached_data:
        if (now - widget.cached_at).seconds < widget.cache_ttl_seconds:
            return widget.cached_data
    # Récupérer les données fraîches
    data = fetch_data(widget)
    widget.cached_data = data
    widget.cached_at = now
    widget.save()
    return data
```

---

## KPIs (Key Performance Indicators)

### Types de KPIs

| Type | Description | Format | Exemple |
|------|-------------|--------|---------|
| **Number** | Valeur absolue | `#,##0` | 1,234 clients |
| **Percentage** | Taux | `#,##0%` | 85% |
| **Currency** | Montant | `€#,##0.00` | 125 000 € |
| **Ratio** | Ratio | `#,##0.00` | 2.5 |
| **Trend** | Évolution | `+15%` | +15% vs mois dernier |
| **Comparison** | Comparaison | `+23%` | 23% mieux que cible |

### Seuils et Statuts

```python
class KPI:
    def get_status(self):
        if self.current_value is None:
            return 'unknown'
        
        # Seuil critique
        if self.critical_threshold is not None:
            if self.current_value >= self.critical_threshold:
                return 'critical'   # 🔴 Critique
        
        # Seuil d'alerte
        if self.warning_threshold is not None:
            if self.current_value >= self.warning_threshold:
                return 'warning'     # ⚠️ Alerte
        
        return 'success'             # ✅ Succès
```

### Calcul des Tendances

```python
# Tendance mensuelle
kpi.track_trend = True
kpi.trend_period = "previous_month"  # previous_month, previous_year, same_month_last_year

# Calcul automatique
result = kpi.calculate()
# {
#     'value': 125000,
#     'previous_value': 100000,
#     'trend': 'up',
#     'trend_percentage': 25.0,
#     'status': 'success'
# }
```

### Formules Personnalisées

```python
# Taux de marge = (CA - Coût) / CA * 100
kpi.formula = "(ca_total - cout_total) / ca_total * 100"
kpi.kpi_type = "percentage"
kpi.format_string = "#,##0.00"
kpi.unit = "%"

# Panier moyen = CA / Nombre de ventes
kpi.formula = "ca_total / nb_ventes"
kpi.kpi_type = "currency"
kpi.format_string = "€#,##0.00"
```

---

## Reports

### Formats d'Export

| Format | Extension | Utilisation |
|--------|-----------|-------------|
| **PNG** | .png | Image pour présentation |
| **SVG** | .svg | Vectoriel haute qualité |
| **PDF** | .pdf | Document officiel |
| **CSV** | .csv | Données brutes pour tableur |
| **Excel** | .xlsx | Analyse poussée |
| **JSON** | .json | Intégration API |
| **HTML** | .html | Page web interactive |
| **Markdown** | .md | Documentation |

### Planification CRON

```python
# Expressions CRON communes
schedules = {
    "every_minute": "* * * * *",
    "every_hour": "0 * * * *",
    "daily_9am": "0 9 * * *",
    "daily_5pm": "0 17 * * *",
    "weekly_monday": "0 9 * * 1",
    "monthly_first": "0 9 1 * *",
    "quarterly": "0 9 1 1,4,7,10 *",
    "yearly": "0 9 1 1 *"
}
```

### Génération de Rapport

```python
# Génération manuelle
result = report.generate(user=request.user)

if result['success']:
    # Fichier généré
    file_content = result['data']
    # Envoi par email
    send_email(report.recipients, file_content)

# Génération programmée
# Les rapports sont automatiquement générés par Celery Beat
```

---

## Favorites

### Gestion des Favoris

```python
# Ajouter un favori
Favorite.objects.add_favorite(user, dashboard, item_type='dashboard', notes='Mon dashboard préféré')

# Ajouter un KPI en favori
Favorite.objects.add_favorite(user, kpi, item_type='kpi')

# Supprimer un favori
Favorite.objects.remove_favorite(user, dashboard, item_type='dashboard')

# Récupérer les favoris d'un utilisateur
favorites = Favorite.objects.for_user(user)

# Réorganiser
for idx, fav in enumerate(favorites):
    fav.order = idx
    fav.save()
```

---

## Activities & Audit

### Types d'Activités

| Activité | Icône | Description | Sévérité |
|----------|-------|-------------|----------|
| **view** | 👁️ | Consultation d'un dashboard | Low |
| **export** | 📤 | Export d'un rapport | Medium |
| **share** | 🔗 | Partage avec d'autres utilisateurs | Medium |
| **edit** | ✏️ | Modification d'un dashboard | High |
| **favorite** | ⭐ | Ajout/suppression de favoris | Low |
| **comment** | 💬 | Ajout de commentaire | Low |

### Journalisation

```python
# Enregistrement automatique
def log_activity(user, dashboard, activity_type, description):
    VisualizationActivity.objects.create(
        user=user,
        dashboard=dashboard,
        activity_type=activity_type,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={
            'timestamp': timezone.now().isoformat(),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'url': request.path
        }
    )

# Statistiques d'activité
stats = VisualizationActivity.objects.stats()
# {
#     'total': 1523,
#     'last_24h': 87,
#     'by_type': {'view': 1200, 'export': 200, 'edit': 123},
#     'by_user': {'admin@mail.com': 450, 'user@mail.com': 300}
# }
```

---

## API Endpoints

### Dashboards
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/visualizations/dashboards/` | Liste des dashboards |
| POST | `/api/visualizations/dashboards/` | Créer un dashboard |
| GET | `/api/visualizations/dashboards/{id}/` | Détails d'un dashboard |
| PUT | `/api/visualizations/dashboards/{id}/` | Mettre à jour |
| DELETE | `/api/visualizations/dashboards/{id}/` | Supprimer |
| GET | `/api/visualizations/dashboards/{id}/render/` | Rendu du dashboard |
| POST | `/api/visualizations/dashboards/{id}/export/` | Export |
| POST | `/api/visualizations/dashboards/{id}/duplicate/` | Dupliquer |
| POST | `/api/visualizations/dashboards/{id}/publish/` | Publier |
| GET | `/api/visualizations/dashboards/stats/` | Statistiques |

### Widgets
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/visualizations/widgets/` | Liste des widgets |
| POST | `/api/visualizations/widgets/` | Créer un widget |
| GET | `/api/visualizations/widgets/{id}/data/` | Données du widget |
| POST | `/api/visualizations/widgets/{id}/render/` | Rendu |
| POST | `/api/visualizations/widgets/{id}/clear-cache/` | Vider le cache |

### KPIs
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/visualizations/kpis/` | Liste des KPIs |
| POST | `/api/visualizations/kpis/` | Créer un KPI |
| POST | `/api/visualizations/kpis/{id}/calculate/` | Calculer la valeur |
| GET | `/api/visualizations/kpis/critical/` | KPIs critiques |
| GET | `/api/visualizations/kpis/warning/` | KPIs en alerte |
| GET | `/api/visualizations/kpis/stats/` | Statistiques |

### Reports
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/visualizations/reports/` | Liste des rapports |
| POST | `/api/visualizations/reports/` | Créer un rapport |
| POST | `/api/visualizations/reports/{id}/generate/` | Générer |
| GET | `/api/visualizations/reports/pending/` | Rapports en attente |
| GET | `/api/visualizations/reports/stats/` | Statistiques |

### Favorites
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/visualizations/favorites/` | Liste des favoris |
| POST | `/api/visualizations/favorites/add/` | Ajouter un favori |
| POST | `/api/visualizations/favorites/remove/` | Supprimer un favori |

### Activities
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/visualizations/activities/` | Liste des activités |
| GET | `/api/visualizations/activities/stats/` | Statistiques |

---

## Usage Examples

### 1. Créer un Dashboard Commercial Complet

```python
from apps.visualizations.models import Dashboard, Widget, KPI
from apps.star_schema.models import DimensionalSchema
from apps.data_warehouse.models import Measure

# 1. Créer le dashboard
dashboard = Dashboard.objects.create(
    name="Dashboard Commercial",
    slug="commercial-dashboard",
    description="Suivi des performances commerciales",
    dashboard_type="analytical",
    status="published",
    theme="light",
    layout={
        "grid": [
            {"x": 0, "y": 0, "w": 6, "h": 4, "widget_id": "ca_trend"},
            {"x": 6, "y": 0, "w": 6, "h": 4, "widget_id": "top_products"},
            {"x": 0, "y": 4, "w": 4, "h": 3, "widget_id": "kpi_ca"},
            {"x": 4, "y": 4, "w": 4, "h": 3, "widget_id": "kpi_marge"},
            {"x": 8, "y": 4, "w": 4, "h": 3, "widget_id": "kpi_panier"}
        ]
    },
    refresh_frequency="hourly",
    access_level="team",
    owner=user,
    team=team_ventes
)

# 2. Récupérer le schéma dimensionnel
schema_ventes = DimensionalSchema.objects.get(name="Analyse des Ventes")
measure_ca = Measure.objects.get(name="Chiffre d'Affaires")

# 3. Créer les widgets
widget_ca_trend = Widget.objects.create(
    name="Évolution du CA",
    widget_type="chart",
    dashboard=dashboard,
    dimensional_schema=schema_ventes,
    config={
        "type": "line",
        "title": "Évolution du Chiffre d'Affaires",
        "x_axis": {"name": "Mois", "field": "date"},
        "y_axis": {"name": "Montant (€)", "field": "montant"}
    },
    position={"x": 0, "y": 0, "w": 6, "h": 4}
)

widget_top_products = Widget.objects.create(
    name="Top Produits",
    widget_type="chart",
    dashboard=dashboard,
    dimensional_schema=schema_ventes,
    config={
        "type": "bar",
        "title": "Top 10 Produits",
        "x_axis": {"name": "Produit", "field": "produit"},
        "y_axis": {"name": "Ventes (€)", "field": "montant"}
    },
    position={"x": 6, "y": 0, "w": 6, "h": 4}
)

# 4. Créer les KPIs
kpi_ca = KPI.objects.create(
    name="Chiffre d'Affaires",
    kpi_type="currency",
    dimensional_schema=schema_ventes,
    measure=measure_ca,
    aggregation="sum",
    target_value=1000000,
    warning_threshold=800000,
    critical_threshold=500000,
    format_string="€#,##0.00",
    unit="EUR",
    track_trend=True,
    dashboard=dashboard
)

kpi_marge = KPI.objects.create(
    name="Marge Brute",
    kpi_type="percentage",
    formula="(ca_total - cout_total) / ca_total * 100",
    target_value=30,
    warning_threshold=25,
    critical_threshold=20,
    format_string="#,##0.00",
    unit="%",
    track_trend=True,
    dashboard=dashboard
)

kpi_panier = KPI.objects.create(
    name="Panier Moyen",
    kpi_type="currency",
    formula="ca_total / nb_transactions",
    target_value=150,
    warning_threshold=120,
    critical_threshold=100,
    format_string="€#,##0.00",
    unit="EUR",
    track_trend=True,
    dashboard=dashboard
)

print(f"Dashboard '{dashboard.name}' créé avec succès!")
```

### 2. Générer un Rapport Mensuel

```python
from apps.visualizations.models import Report

# Créer le rapport
report = Report.objects.create(
    name="Rapport Commercial Mensuel",
    description="Synthèse des performances commerciales du mois",
    dashboard=dashboard,
    format="pdf",
    schedule="0 9 1 * *",  # 1er du mois à 9h
    recipients=[
        "direction@entreprise.com",
        "commercial@entreprise.com"
    ],
    filters={"date_range": "last_month"},
    include_metadata=True,
    include_filters=True,
    page_size="A4",
    orientation="landscape"
)

# Génération immédiate
result = report.generate()

if result['success']:
    print(f"Rapport généré en {result['execution_time_ms']}ms")
else:
    print(f"Erreur: {result['error']}")
```

### 3. API Requests

```bash
# Récupérer tous les dashboards
curl -X GET "http://localhost:8000/api/visualizations/dashboards/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Créer un nouveau dashboard
curl -X POST "http://localhost:8000/api/visualizations/dashboards/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dashboard Ventes",
    "description": "Suivi des ventes",
    "dashboard_type": "analytical",
    "theme": "light",
    "access_level": "team"
  }'

# Rendre un dashboard
curl -X GET "http://localhost:8000/api/visualizations/dashboards/{id}/render/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Exporter un dashboard en PDF
curl -X POST "http://localhost:8000/api/visualizations/dashboards/{id}/export/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format": "pdf"}'

# Calculer un KPI
curl -X POST "http://localhost:8000/api/visualizations/kpis/{id}/calculate/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filters": {"date": "2024-03-01"}}'

# Générer un rapport
curl -X POST "http://localhost:8000/api/visualizations/reports/{id}/generate/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Best Practices

### 1. Nommage des Dashboards

| Type | Convention | Exemple |
|------|------------|---------|
| Analytique | `{domaine}_analysis` | `sales_analysis` |
| Opérationnel | `{domaine}_ops` | `sales_ops` |
| Exécutif | `{domaine}_exec` | `sales_exec` |
| Stratégique | `{domaine}_strategy` | `sales_strategy` |

### 2. Organisation des Widgets

```python
# Recommandations de taille
widget_sizes = {
    "kpi": {"min_w": 2, "max_w": 4, "h": 3},      # Petits KPIs
    "chart": {"min_w": 4, "max_w": 12, "h": 6},    # Graphiques
    "table": {"min_w": 6, "max_w": 12, "h": 8},    # Tableaux
    "text": {"min_w": 3, "max_w": 12, "h": 3}      # Textes
}
```

### 3. Configuration du Cache

```python
# Stratégies de cache
cache_strategies = {
    "realtime": {"enabled": False, "ttl": 0},           # Temps réel
    "minute": {"enabled": True, "ttl": 60},              # 1 minute
    "hourly": {"enabled": True, "ttl": 3600},            # 1 heure
    "daily": {"enabled": True, "ttl": 86400}             # 1 jour
}
```

### 4. Gestion des Permissions

```python
# Vérifier l'accès avant rendu
def can_view_dashboard(user, dashboard):
    if user.is_superuser:
        return True
    if dashboard.access_level == 'private' and dashboard.owner != user:
        return False
    if dashboard.access_level == 'team' and user not in dashboard.team.members:
        return False
    if dashboard.access_level == 'organization':
        return True
    return True
```

---

## Performance Optimization

### 1. Cache des Données

```python
# Configurer le cache pour les widgets fréquents
widget.cache_enabled = True
widget.cache_ttl_seconds = 3600  # 1 heure

# Invalider le cache après mise à jour
@receiver(post_save, sender=Widget)
def invalidate_widget_cache(sender, instance, **kwargs):
    cache.delete(f"widget_data_{instance.id}")
```

### 2. Optimisation des Requêtes

```python
# Utiliser select_related et prefetch_related
dashboards = Dashboard.objects.select_related('owner', 'team').prefetch_related(
    'widgets', 'kpis', 'reports'
)

# Pagination
from rest_framework.pagination import PageNumberPagination

class DashboardPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100
```

### 3. Rendu Asynchrone

```python
# Rendu asynchrone des widgets
import asyncio
from concurrent.futures import ThreadPoolExecutor

def render_widgets_async(widgets):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(render_widget, widgets)
    return list(results)
```

### 4. Compression des Réponses

```python
# Activer la compression GZIP
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    # ...
]
```

---

## Troubleshooting

### Problèmes Courants

| Problème | Cause | Solution |
|----------|-------|----------|
| **Widget ne s'affiche pas** | Configuration invalide | Vérifier `config` JSON |
| **KPI ne se calcule pas** | Source de données absente | Vérifier `dimensional_schema` et `measure` |
| **Rapport non généré** | Format non supporté | Utiliser format PDF, CSV, Excel |
| **Cache trop vieux** | TTL trop long | Réduire `cache_ttl_seconds` |
| **Permissions refusées** | Accès non configuré | Vérifier `access_level` |

### Débogage

```python
# Activer les logs de débogage
import logging
logging.getLogger('apps.visualizations').setLevel(logging.DEBUG)

# Vérifier les données d'un widget
widget_data = widget.get_data()
print(f"Données: {len(widget_data)} lignes")

# Tester un KPI
result = kpi.calculate()
print(f"Valeur: {result['value']}")
print(f"Tendance: {result['trend_percentage']}%")
print(f"Statut: {kpi.get_status()}")

# Vérifier le SQL généré
sql = dashboard.generate_query()
print(sql)

# Voir les activités récentes
activities = VisualizationActivity.objects.filter(
    dashboard=dashboard
).order_by('-created_at')[:10]

for activity in activities:
    print(f"{activity.created_at}: {activity.user} - {activity.activity_type}")
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Version avec dashboards, widgets, KPIs, rapports, favoris et activités |
```

Ce fichier de documentation doit être sauvegardé dans :
```
/home/user/sotifibre/sotifibre_backend_django/docs/modules/visualizations.md
```