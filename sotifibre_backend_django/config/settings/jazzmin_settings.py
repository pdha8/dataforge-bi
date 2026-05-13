"""
Jazzmin Admin Settings for Sotifibre BI - Core, Users, Data Sources, ETL Engine, Data Warehouse, Star Schema, Visualizations & Notifications
"""
JAZZMIN_SETTINGS = {
    # ========================================================================
    # BRANDING
    # ========================================================================
    "site_title": "Sotifibre BI Platform",
    "site_header": "Sotifibre Administrator",
    "site_brand": "📊 Sotifibre BI",
    "site_logo": None,
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "🌟 Welcome to Sotifibre - Business Intelligence Platform",
    "copyright": "Sotifibre Analytics 2026 | v1.0.0",    
    
    # ========================================================================
    # TOP MENU LINKS
    # ========================================================================
    "topmenu_links": [
        {"name": "🏠 Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "🗄️ Data Sources", "url": "/admin/data_sources/", "new_window": False},
        {"name": "🔄 ETL Engine", "url": "/admin/etl_engine/", "new_window": False},
        {"name": "🏢 Data Warehouse", "url": "/admin/data_warehouse/", "new_window": False},
        {"name": "⭐ Star Schema", "url": "/admin/star_schema/", "new_window": False},
        {"name": "📊 Visualizations", "url": "/admin/visualizations/", "new_window": False},
        {"name": "🔔 Notifications", "url": "/admin/notifications/", "new_window": False},
        {"name": "📈 KPIs", "url": "/admin/kpis/", "new_window": False},
        {"name": "📑 Reports", "url": "/admin/reports/", "new_window": False},
        {"name": "📚 API Docs", "url": "/api/schema/swagger-ui/", "new_window": True},
        {"name": "📖 ReDoc", "url": "/api/schema/redoc/", "new_window": True},
        {"name": "📧 Support", "url": "mailto:support@sotifibre.com", "new_window": True},
    ],
    
    # ========================================================================
    # USER MENU LINKS
    # ========================================================================
    "usermenu_links": [
        {"model": "users.user"},
        {"name": "🔐 My Profile", "url": "/admin/users/user/", "icon": "fas fa-user-circle"},
        {"name": "⚙️ Account Settings", "url": "/admin/account/", "icon": "fas fa-cog"},
        {"name": "📄 Documentation", "url": "https://docs.sotifibre.com", "new_window": True},
    ],
    
    # ========================================================================
    # SIDEBAR CONFIGURATION
    # ========================================================================
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [],
    
    # ========================================================================
    # ORDER WITH RESPECT TO - Organisation hiérarchique
    # ========================================================================
    "order_with_respect_to": [
        "users",           # Section 1: Gestion des utilisateurs BI
        "core",            # Section 2: Configuration Core
        "data_sources",    # Section 3: Sources de données BI
        "etl_engine",      # Section 4: Moteur ETL
        "data_warehouse",  # Section 5: Data Warehouse
        "star_schema",     # Section 6: Star Schema
        "visualizations",  # Section 7: Visualizations
        "notifications",   # Section 8: Notifications ← NOUVEAU
        "auth",            # Section 9: Authentification
        "authtoken",       
        "token_blacklist",
        "django_celery_beat",
        "django_celery_results",
    ],
    
    # ========================================================================
    # ICONS - Tous les modèles
    # ========================================================================
    "icons": {
        # SECTION 1: GESTION DES UTILISATEURS BI
        "users": "fas fa-users-cog",
        "users.User": "fas fa-user-circle",
        "users.Team": "fas fa-users",
        "users.Role": "fas fa-user-tag",
        "users.Permission": "fas fa-key",
        "users.UserActivity": "fas fa-history",
        
        # SECTION 2: CORE
        "core": "fas fa-cogs",
        "core.Config": "fas fa-sliders-h",
        
        # SECTION 3: SOURCES DE DONNÉES
        "data_sources": "fas fa-database",
        "data_sources.DataSource": "fas fa-database",
        "data_sources.DataTable": "fas fa-table",
        "data_sources.DataQuery": "fas fa-code",
        "data_sources.DataSourceFile": "fas fa-file-upload",
        "data_sources.DataSourceConnection": "fas fa-plug",
        "data_sources.PowerQuery": "fas fa-chart-line",
        "data_sources.QueryStep": "fas fa-code-branch",
        "data_sources.StarSchema": "fas fa-star-of-life",
        "data_sources.DataSourceLog": "fas fa-history",
        "data_sources.DataSourceMetric": "fas fa-chart-line",
        "data_sources.DataSourceHistory": "fas fa-clock",
        
        # SECTION 4: ETL ENGINE
        "etl_engine": "fas fa-exchange-alt",
        "etl_engine.ETLPipeline": "fas fa-code-branch",
        "etl_engine.Transformation": "fas fa-filter",
        "etl_engine.ExecutionLog": "fas fa-history",
        "etl_engine.TargetSchema": "fas fa-table",
        "etl_engine.SourceSchema": "fas fa-database",
        "etl_engine.PipelineNotification": "fas fa-bell",
        
        # SECTION 5: DATA WAREHOUSE
        "data_warehouse": "fas fa-warehouse",
        "data_warehouse.DataWarehouseSchema": "fas fa-draw-polygon",
        "data_warehouse.DataWarehouseTable": "fas fa-table",
        "data_warehouse.DimensionTable": "fas fa-cube",
        "data_warehouse.FactTable": "fas fa-chart-simple",
        "data_warehouse.DimensionAttribute": "fas fa-list-ul",
        "data_warehouse.Measure": "fas fa-chart-line",
        "data_warehouse.StarSchema": "fas fa-star-of-life",
        "data_warehouse.AggregationTable": "fas fa-chart-pie",
        "data_warehouse.DataWarehouseMetric": "fas fa-chart-simple",
        "data_warehouse.DataWarehouseLog": "fas fa-history",
        
        # SECTION 6: STAR SCHEMA
        "star_schema": "fas fa-star-of-life",
        "star_schema.DimensionalSchema": "fas fa-cubes",
        "star_schema.CustomCalculation": "fas fa-calculator",
        "star_schema.DimensionHierarchy": "fas fa-sitemap",
        "star_schema.FactRelationship": "fas fa-link",
        "star_schema.GalaxySchema": "fas fa-globe",
        
        # SECTION 7: VISUALIZATIONS
        "visualizations": "fas fa-chart-line",
        "visualizations.Dashboard": "fas fa-tachometer-alt",
        "visualizations.Widget": "fas fa-chart-pie",
        "visualizations.KPI": "fas fa-chart-simple",
        "visualizations.Report": "fas fa-file-alt",
        "visualizations.Favorite": "fas fa-star",
        "visualizations.VisualizationActivity": "fas fa-history",
        
        # SECTION 8: NOTIFICATIONS ← NOUVEAU
        "notifications": "fas fa-bell",
        "notifications.Notification": "fas fa-envelope",
        "notifications.NotificationChannel": "fas fa-plug",
        "notifications.Subscription": "fas fa-rss",
        "notifications.AlertRule": "fas fa-exclamation-triangle",
        
        # SECTION 9: AUTHENTIFICATION
        "auth": "fas fa-lock",
        "auth.Group": "fas fa-users-cog",
        "auth.Permission": "fas fa-key",
        
        # SECTION 10: TOKENS
        "authtoken": "fas fa-key",
        "authtoken.Token": "fas fa-token",
        "authtoken.tokenproxy": "fas fa-key",
        
        # SECTION 11: TOKEN BLACKLIST
        "token_blacklist": "fas fa-ban",
        "token_blacklist.BlacklistedToken": "fas fa-ban",
        "token_blacklist.OutstandingToken": "fas fa-clock",
        
        # SECTION 12: CELERY BEAT
        "django_celery_beat": "fas fa-clock",
        "django_celery_beat.ClockedSchedule": "fas fa-clock",
        "django_celery_beat.CrontabSchedule": "fas fa-calendar-alt",
        "django_celery_beat.IntervalSchedule": "fas fa-hourglass",
        "django_celery_beat.PeriodicTask": "fas fa-tasks",
        "django_celery_beat.PeriodicTasks": "fas fa-list",
        "django_celery_beat.SolarSchedule": "fas fa-sun",
        
        # SECTION 13: CELERY RESULTS
        "django_celery_results": "fas fa-chart-line",
        "django_celery_results.TaskResult": "fas fa-check-circle",
        "django_celery_results.GroupResult": "fas fa-layer-group",
        "django_celery_results.ChordCounter": "fas fa-code-branch",
    },
    
    # ========================================================================
    # DEFAULT ICONS
    # ========================================================================
    "default_icon_parents": "fas fa-folder-open",
    "default_icon_children": "fas fa-file",
    
    # ========================================================================
    # CUSTOM LINKS - Liens rapides
    # ========================================================================
    "custom_links": {
        "users": [
            {"name": "➕ Créer utilisateur BI", "url": "/admin/users/user/add/", "icon": "fas fa-user-plus", "permissions": ["users.add_user"]},
            {"name": "👥 Nouvelle équipe", "url": "/admin/users/team/add/", "icon": "fas fa-users", "permissions": ["users.add_team"]},
            {"name": "🎭 Nouveau rôle BI", "url": "/admin/users/role/add/", "icon": "fas fa-user-tag", "permissions": ["users.add_role"]},
            {"name": "🔑 Nouvelle permission", "url": "/admin/users/permission/add/", "icon": "fas fa-key", "permissions": ["users.add_permission"]},
            {"name": "📊 Voir activités", "url": "/admin/users/useractivity/", "icon": "fas fa-history", "permissions": ["users.view_useractivity"]},
        ],
        "core": [
            {"name": "⚙️ Nouvelle configuration", "url": "/admin/core/config/add/", "icon": "fas fa-plus-circle", "permissions": ["core.add_config"]},
            {"name": "📋 Voir configurations", "url": "/admin/core/config/", "icon": "fas fa-list", "permissions": ["core.view_config"]},
        ],
        "data_sources": [
            {"name": "🗄️ Nouvelle source", "url": "/admin/data_sources/datasource/add/", "icon": "fas fa-plus-circle", "permissions": ["data_sources.add_datasource"]},
            {"name": "📁 Upload fichier", "url": "/admin/data_sources/datasourcefile/add/", "icon": "fas fa-file-upload", "permissions": ["data_sources.add_datasourcefile"]},
            {"name": "🔌 Nouvelle connexion", "url": "/admin/data_sources/datasourceconnection/add/", "icon": "fas fa-plug", "permissions": ["data_sources.add_datasourceconnection"]},
            {"name": "📊 Nouveau Power Query", "url": "/admin/data_sources/powerquery/add/", "icon": "fas fa-chart-line", "permissions": ["data_sources.add_powerquery"]},
            {"name": "⭐ Nouveau schéma en étoile", "url": "/admin/data_sources/starschema/add/", "icon": "fas fa-star-of-life", "permissions": ["data_sources.add_starschema"]},
            {"name": "📋 Voir toutes les sources", "url": "/admin/data_sources/datasource/", "icon": "fas fa-list", "permissions": ["data_sources.view_datasource"]},
            {"name": "📈 Voir métriques", "url": "/admin/data_sources/datasourcemetric/", "icon": "fas fa-chart-line", "permissions": ["data_sources.view_datasourcemetric"]},
            {"name": "📝 Voir logs", "url": "/admin/data_sources/datasourcelog/", "icon": "fas fa-history", "permissions": ["data_sources.view_datasourcelog"]},
        ],
        "etl_engine": [
            {"name": "🔄 Nouveau pipeline", "url": "/admin/etl_engine/etlpipeline/add/", "icon": "fas fa-plus-circle", "permissions": ["etl_engine.add_etlpipeline"]},
            {"name": "⚙️ Nouvelle transformation", "url": "/admin/etl_engine/transformation/add/", "icon": "fas fa-filter", "permissions": ["etl_engine.add_transformation"]},
            {"name": "📊 Voir exécutions", "url": "/admin/etl_engine/executionlog/", "icon": "fas fa-history", "permissions": ["etl_engine.view_executionlog"]},
            {"name": "📋 Voir tous les pipelines", "url": "/admin/etl_engine/etlpipeline/", "icon": "fas fa-list", "permissions": ["etl_engine.view_etlpipeline"]},
            {"name": "🎯 Schémas cibles", "url": "/admin/etl_engine/targetschema/", "icon": "fas fa-table", "permissions": ["etl_engine.view_targetschema"]},
            {"name": "📁 Schémas sources", "url": "/admin/etl_engine/sourceschema/", "icon": "fas fa-database", "permissions": ["etl_engine.view_sourceschema"]},
            {"name": "🔔 Notifications", "url": "/admin/etl_engine/pipelinenotification/", "icon": "fas fa-bell", "permissions": ["etl_engine.view_pipelinenotification"]},
            {"name": "▶️ Exécuter pipeline", "url": "/admin/etl_engine/etlpipeline/", "icon": "fas fa-play", "permissions": ["etl_engine.change_etlpipeline"]},
        ],
        "data_warehouse": [
            {"name": "🏢 Nouveau schéma", "url": "/admin/data_warehouse/datawarehouseschema/add/", "icon": "fas fa-plus-circle", "permissions": ["data_warehouse.add_datawarehouseschema"]},
            {"name": "📊 Nouvelle table", "url": "/admin/data_warehouse/datawarehousetable/add/", "icon": "fas fa-plus-circle", "permissions": ["data_warehouse.add_datawarehousetable"]},
            {"name": "📐 Nouvelle dimension", "url": "/admin/data_warehouse/dimensiontable/add/", "icon": "fas fa-cube", "permissions": ["data_warehouse.add_dimensiontable"]},
            {"name": "📈 Nouvelle table de faits", "url": "/admin/data_warehouse/facttable/add/", "icon": "fas fa-chart-simple", "permissions": ["data_warehouse.add_facttable"]},
            {"name": "⭐ Nouveau schéma en étoile", "url": "/admin/data_warehouse/starschema/add/", "icon": "fas fa-star-of-life", "permissions": ["data_warehouse.add_starschema"]},
            {"name": "📊 Nouvelle mesure", "url": "/admin/data_warehouse/measure/add/", "icon": "fas fa-chart-line", "permissions": ["data_warehouse.add_measure"]},
            {"name": "📋 Attributs de dimension", "url": "/admin/data_warehouse/dimensionattribute/add/", "icon": "fas fa-list-ul", "permissions": ["data_warehouse.add_dimensionattribute"]},
            {"name": "📦 Agrégations", "url": "/admin/data_warehouse/aggregationtable/add/", "icon": "fas fa-chart-pie", "permissions": ["data_warehouse.add_aggregationtable"]},
            {"name": "📈 Métriques DW", "url": "/admin/data_warehouse/datawarehousemetric/", "icon": "fas fa-chart-simple", "permissions": ["data_warehouse.view_datawarehousemetric"]},
            {"name": "📝 Logs DW", "url": "/admin/data_warehouse/datawarehouselog/", "icon": "fas fa-history", "permissions": ["data_warehouse.view_datawarehouselog"]},
            {"name": "📋 Voir tous les schémas", "url": "/admin/data_warehouse/datawarehouseschema/", "icon": "fas fa-list", "permissions": ["data_warehouse.view_datawarehouseschema"]},
            {"name": "📊 Voir toutes les tables", "url": "/admin/data_warehouse/datawarehousetable/", "icon": "fas fa-table", "permissions": ["data_warehouse.view_datawarehousetable"]},
        ],
        "star_schema": [
            {"name": "⭐ Nouveau schéma dimensionnel", "url": "/admin/star_schema/dimensionalschema/add/", "icon": "fas fa-plus-circle", "permissions": ["star_schema.add_dimensionalschema"]},
            {"name": "📐 Nouvelle hiérarchie", "url": "/admin/star_schema/dimensionhierarchy/add/", "icon": "fas fa-sitemap", "permissions": ["star_schema.add_dimensionhierarchy"]},
            {"name": "🔗 Nouvelle relation", "url": "/admin/star_schema/factrelationship/add/", "icon": "fas fa-link", "permissions": ["star_schema.add_factrelationship"]},
            {"name": "🧮 Nouveau calcul", "url": "/admin/star_schema/customcalculation/add/", "icon": "fas fa-calculator", "permissions": ["star_schema.add_customcalculation"]},
            {"name": "🌌 Nouvelle galaxie", "url": "/admin/star_schema/galaxyschema/add/", "icon": "fas fa-globe", "permissions": ["star_schema.add_galaxyschema"]},
            {"name": "📋 Voir tous les schémas", "url": "/admin/star_schema/dimensionalschema/", "icon": "fas fa-list", "permissions": ["star_schema.view_dimensionalschema"]},
            {"name": "📊 Voir les relations", "url": "/admin/star_schema/factrelationship/", "icon": "fas fa-link", "permissions": ["star_schema.view_factrelationship"]},
            {"name": "📈 Voir les calculs", "url": "/admin/star_schema/customcalculation/", "icon": "fas fa-calculator", "permissions": ["star_schema.view_customcalculation"]},
            {"name": "🌍 Voir les galaxies", "url": "/admin/star_schema/galaxyschema/", "icon": "fas fa-globe", "permissions": ["star_schema.view_galaxyschema"]},
        ],
        "visualizations": [
            {"name": "📊 Nouveau tableau de bord", "url": "/admin/visualizations/dashboard/add/", "icon": "fas fa-plus-circle", "permissions": ["visualizations.add_dashboard"]},
            {"name": "📈 Nouveau KPI", "url": "/admin/visualizations/kpi/add/", "icon": "fas fa-chart-simple", "permissions": ["visualizations.add_kpi"]},
            {"name": "📄 Nouveau rapport", "url": "/admin/visualizations/report/add/", "icon": "fas fa-file-alt", "permissions": ["visualizations.add_report"]},
            {"name": "🧩 Nouveau widget", "url": "/admin/visualizations/widget/add/", "icon": "fas fa-chart-pie", "permissions": ["visualizations.add_widget"]},
            {"name": "⭐ Gérer favoris", "url": "/admin/visualizations/favorite/", "icon": "fas fa-star", "permissions": ["visualizations.view_favorite"]},
            {"name": "📊 Voir tous les dashboards", "url": "/admin/visualizations/dashboard/", "icon": "fas fa-list", "permissions": ["visualizations.view_dashboard"]},
            {"name": "📈 Voir tous les KPIs", "url": "/admin/visualizations/kpi/", "icon": "fas fa-chart-line", "permissions": ["visualizations.view_kpi"]},
            {"name": "📄 Voir tous les rapports", "url": "/admin/visualizations/report/", "icon": "fas fa-file-alt", "permissions": ["visualizations.view_report"]},
            {"name": "📝 Voir activités", "url": "/admin/visualizations/visualizationactivity/", "icon": "fas fa-history", "permissions": ["visualizations.view_visualizationactivity"]},
        ],
        "notifications": [  # ← NOUVEAU SECTION NOTIFICATIONS
            {"name": "🔔 Nouvelle notification", "url": "/admin/notifications/notification/add/", "icon": "fas fa-plus-circle", "permissions": ["notifications.add_notification"]},
            {"name": "📢 Nouvelle règle d'alerte", "url": "/admin/notifications/alertrule/add/", "icon": "fas fa-exclamation-triangle", "permissions": ["notifications.add_alertrule"]},
            {"name": "🔌 Nouveau canal", "url": "/admin/notifications/notificationchannel/add/", "icon": "fas fa-plug", "permissions": ["notifications.add_notificationchannel"]},
            {"name": "📡 Nouvel abonnement", "url": "/admin/notifications/subscription/add/", "icon": "fas fa-rss", "permissions": ["notifications.add_subscription"]},
            {"name": "🔔 Voir toutes les notifications", "url": "/admin/notifications/notification/", "icon": "fas fa-list", "permissions": ["notifications.view_notification"]},
            {"name": "⚠️ Voir les règles d'alerte", "url": "/admin/notifications/alertrule/", "icon": "fas fa-exclamation-triangle", "permissions": ["notifications.view_alertrule"]},
            {"name": "🔌 Voir les canaux", "url": "/admin/notifications/notificationchannel/", "icon": "fas fa-plug", "permissions": ["notifications.view_notificationchannel"]},
            {"name": "📡 Voir les abonnements", "url": "/admin/notifications/subscription/", "icon": "fas fa-rss", "permissions": ["notifications.view_subscription"]},
        ],
    },
    
    # ========================================================================
    # RELATED MODAL
    # ========================================================================
    "related_modal_active": True,
    
    # ========================================================================
    # CUSTOM CSS/JS
    # ========================================================================
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    
    # ========================================================================
    # CHANGE FORM FORMAT
    # ========================================================================
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        # Users
        "users.user": "vertical_tabs",
        "users.team": "horizontal_tabs",
        "users.role": "collapsible",
        "users.permission": "collapsible",
        "users.useractivity": "collapsible",
        
        # Core
        "core.config": "horizontal_tabs",
        
        # Data Sources
        "data_sources.datasource": "vertical_tabs",
        "data_sources.datatable": "horizontal_tabs",
        "data_sources.dataquery": "horizontal_tabs",
        "data_sources.datasourcefile": "vertical_tabs",
        "data_sources.datasourceconnection": "horizontal_tabs",
        "data_sources.powerquery": "vertical_tabs",
        "data_sources.querystep": "collapsible",
        "data_sources.starschema": "vertical_tabs",
        "data_sources.datasourcelog": "collapsible",
        "data_sources.datasourcemetric": "collapsible",
        "data_sources.datasourcehistory": "collapsible",
        
        # ETL Engine
        "etl_engine.etlpipeline": "vertical_tabs",
        "etl_engine.transformation": "horizontal_tabs",
        "etl_engine.executionlog": "collapsible",
        "etl_engine.targetschema": "horizontal_tabs",
        "etl_engine.sourceschema": "horizontal_tabs",
        "etl_engine.pipelinenotification": "collapsible",
        
        # Data Warehouse
        "data_warehouse.datawarehouseschema": "vertical_tabs",
        "data_warehouse.datawarehousetable": "vertical_tabs",
        "data_warehouse.dimensiontable": "vertical_tabs",
        "data_warehouse.facttable": "vertical_tabs",
        "data_warehouse.dimensionattribute": "horizontal_tabs",
        "data_warehouse.measure": "horizontal_tabs",
        "data_warehouse.starschema": "vertical_tabs",
        "data_warehouse.aggregationtable": "horizontal_tabs",
        "data_warehouse.datawarehousemetric": "collapsible",
        "data_warehouse.datawarehouselog": "collapsible",
        
        # Star Schema
        "star_schema.dimensionalschema": "vertical_tabs",
        "star_schema.customcalculation": "horizontal_tabs",
        "star_schema.dimensionhierarchy": "horizontal_tabs",
        "star_schema.factrelationship": "horizontal_tabs",
        "star_schema.galaxyschema": "vertical_tabs",
        
        # Visualizations
        "visualizations.dashboard": "vertical_tabs",
        "visualizations.widget": "horizontal_tabs",
        "visualizations.kpi": "vertical_tabs",
        "visualizations.report": "horizontal_tabs",
        "visualizations.favorite": "collapsible",
        "visualizations.visualizationactivity": "collapsible",
        
        # Notifications ← NOUVEAU
        "notifications.notification": "vertical_tabs",
        "notifications.notificationchannel": "horizontal_tabs",
        "notifications.subscription": "horizontal_tabs",
        "notifications.alertrule": "vertical_tabs",
        
        # Celery
        "django_celery_beat.periodictask": "horizontal_tabs",
        "django_celery_beat.crontabschedule": "collapsible",
        "django_celery_beat.intervalschedule": "collapsible",
        
        # Token Blacklist
        "token_blacklist.blacklistedtoken": "collapsible",
        "token_blacklist.outstandingtoken": "collapsible",
    },
    
    # ========================================================================
    # LANGUAGE - Désactivé
    # ========================================================================
    "language_chooser": False,
}

# ========================================================================
# JAZZMIN UI TWEAKS
# ========================================================================
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar_small_text": False,
    "navbar_fixed": True,
    "navbar": "navbar-light bg-white",
    "navbar_class": "shadow-sm border-bottom",
    "sidebar": "sidebar-light-primary",
    "sidebar_fixed": True,
    "sidebar_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "footer_fixed": False,
    "footer_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-light",
    "brand_colour_bg": "bg-white",
    "body_small_text": False,
    "no_navbar_border": False,
    "layout_boxed": False,
    "accent": "accent-primary",
    "button_classes": {
        "primary": "btn-primary btn-sm",
        "secondary": "btn-secondary btn-sm",
        "info": "btn-info btn-sm",
        "warning": "btn-warning btn-sm",
        "danger": "btn-danger btn-sm",
        "success": "btn-success btn-sm",
        "outline-primary": "btn-outline-primary btn-sm",
    },
    "actions_sticky_top": True,
}

# ========================================================================
# CUSTOM DASHBOARD - Tableau de bord personnalisé
# ========================================================================
JAZZMIN_DASHBOARD = {
    "welcome_message": """
        <div class="alert alert-primary alert-dismissible fade show" role="alert">
            <strong>👋 Welcome back, {user}!</strong>
            <span class="badge bg-success ms-2">{active_users}/{total_users} users active</span>
            <span class="badge bg-info ms-2">{total_teams} teams</span>
            <span class="badge bg-secondary ms-2">{total_roles} roles</span>
            <span class="badge bg-warning ms-2">{activities_24h} activities</span>
            <span class="badge bg-primary ms-2">{total_configs} configs</span>
            <span class="badge bg-purple ms-2">{api_users} API users</span>
            <span class="badge bg-success ms-2">{total_sources} data sources</span>
            <span class="badge bg-info ms-2">{active_sources} active</span>
            <span class="badge bg-danger ms-2">{error_sources} errors</span>
            <span class="badge bg-success ms-2">{active_pipelines} pipelines</span>
            <span class="badge bg-info ms-2">{total_executions} executions</span>
            <span class="badge bg-primary ms-2">{total_schemas} DW schemas</span>
            <span class="badge bg-warning ms-2">{total_dw_tables} DW tables</span>
            <span class="badge bg-success ms-2">{total_dimensional_schemas} dimensional schemas</span>
            <span class="badge bg-info ms-2">{total_galaxies} galaxies</span>
            <span class="badge bg-success ms-2">{total_dashboards} dashboards</span>
            <span class="badge bg-info ms-2">{total_kpis} KPIs</span>
            <span class="badge bg-warning ms-2">{total_notifications} notifications</span>
            <span class="badge bg-danger ms-2">{unread_notifications} unread</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    """,
    
    "quick_actions": [
        # Users
        {"name": "➕ Create User", "url": "/admin/users/user/add/", "icon": "fas fa-user-plus", "color": "success"},
        {"name": "👥 New Team", "url": "/admin/users/team/add/", "icon": "fas fa-users", "color": "primary"},
        {"name": "🎭 New Role", "url": "/admin/users/role/add/", "icon": "fas fa-user-tag", "color": "info"},
        {"name": "🔑 New Permission", "url": "/admin/users/permission/add/", "icon": "fas fa-key", "color": "warning"},
        
        # Core
        {"name": "⚙️ New Config", "url": "/admin/core/config/add/", "icon": "fas fa-sliders-h", "color": "secondary"},
        {"name": "📋 View Configs", "url": "/admin/core/config/", "icon": "fas fa-list", "color": "dark"},
        
        # Data Sources
        {"name": "🗄️ New Data Source", "url": "/admin/data_sources/datasource/add/", "icon": "fas fa-database", "color": "success"},
        {"name": "📁 Upload File", "url": "/admin/data_sources/datasourcefile/add/", "icon": "fas fa-file-upload", "color": "info"},
        {"name": "📊 New Power Query", "url": "/admin/data_sources/powerquery/add/", "icon": "fas fa-chart-line", "color": "primary"},
        {"name": "⭐ New Star Schema", "url": "/admin/data_sources/starschema/add/", "icon": "fas fa-star-of-life", "color": "warning"},
        {"name": "🔌 Test Connection", "url": "/admin/data_sources/datasource/", "icon": "fas fa-plug", "color": "danger"},
        
        # ETL Engine
        {"name": "🔄 New Pipeline", "url": "/admin/etl_engine/etlpipeline/add/", "icon": "fas fa-code-branch", "color": "success"},
        {"name": "⚙️ New Transformation", "url": "/admin/etl_engine/transformation/add/", "icon": "fas fa-filter", "color": "info"},
        {"name": "▶️ Execute Pipeline", "url": "/admin/etl_engine/etlpipeline/", "icon": "fas fa-play", "color": "primary"},
        {"name": "📊 View Executions", "url": "/admin/etl_engine/executionlog/", "icon": "fas fa-history", "color": "warning"},
        {"name": "🔔 Configure Notifications", "url": "/admin/etl_engine/pipelinenotification/add/", "icon": "fas fa-bell", "color": "danger"},
        
        # Data Warehouse
        {"name": "🏢 New DW Schema", "url": "/admin/data_warehouse/datawarehouseschema/add/", "icon": "fas fa-draw-polygon", "color": "success"},
        {"name": "📊 New DW Table", "url": "/admin/data_warehouse/datawarehousetable/add/", "icon": "fas fa-table", "color": "primary"},
        {"name": "📐 New Dimension", "url": "/admin/data_warehouse/dimensiontable/add/", "icon": "fas fa-cube", "color": "info"},
        {"name": "📈 New Fact Table", "url": "/admin/data_warehouse/facttable/add/", "icon": "fas fa-chart-simple", "color": "warning"},
        {"name": "⭐ New Star Schema", "url": "/admin/data_warehouse/starschema/add/", "icon": "fas fa-star-of-life", "color": "danger"},
        {"name": "📊 New Measure", "url": "/admin/data_warehouse/measure/add/", "icon": "fas fa-chart-line", "color": "secondary"},
        {"name": "📦 New Aggregation", "url": "/admin/data_warehouse/aggregationtable/add/", "icon": "fas fa-chart-pie", "color": "dark"},
        {"name": "📈 View DW Metrics", "url": "/admin/data_warehouse/datawarehousemetric/", "icon": "fas fa-chart-simple", "color": "info"},
        
        # Star Schema
        {"name": "⭐ New Dimensional Schema", "url": "/admin/star_schema/dimensionalschema/add/", "icon": "fas fa-cubes", "color": "success"},
        {"name": "📐 New Hierarchy", "url": "/admin/star_schema/dimensionhierarchy/add/", "icon": "fas fa-sitemap", "color": "info"},
        {"name": "🔗 New Relationship", "url": "/admin/star_schema/factrelationship/add/", "icon": "fas fa-link", "color": "warning"},
        {"name": "🧮 New Calculation", "url": "/admin/star_schema/customcalculation/add/", "icon": "fas fa-calculator", "color": "primary"},
        {"name": "🌌 New Galaxy", "url": "/admin/star_schema/galaxyschema/add/", "icon": "fas fa-globe", "color": "danger"},
        
        # Visualizations
        {"name": "📊 New Dashboard", "url": "/admin/visualizations/dashboard/add/", "icon": "fas fa-tachometer-alt", "color": "success"},
        {"name": "📈 New KPI", "url": "/admin/visualizations/kpi/add/", "icon": "fas fa-chart-simple", "color": "primary"},
        {"name": "📄 New Report", "url": "/admin/visualizations/report/add/", "icon": "fas fa-file-alt", "color": "info"},
        {"name": "🧩 New Widget", "url": "/admin/visualizations/widget/add/", "icon": "fas fa-chart-pie", "color": "warning"},
        {"name": "⭐ View Favorites", "url": "/admin/visualizations/favorite/", "icon": "fas fa-star", "color": "danger"},
        {"name": "📊 View All Dashboards", "url": "/admin/visualizations/dashboard/", "icon": "fas fa-list", "color": "secondary"},
        
        # Notifications ← NOUVEAU
        {"name": "🔔 New Notification", "url": "/admin/notifications/notification/add/", "icon": "fas fa-bell", "color": "success"},
        {"name": "⚠️ New Alert Rule", "url": "/admin/notifications/alertrule/add/", "icon": "fas fa-exclamation-triangle", "color": "danger"},
        {"name": "🔌 New Channel", "url": "/admin/notifications/notificationchannel/add/", "icon": "fas fa-plug", "color": "info"},
        {"name": "📡 New Subscription", "url": "/admin/notifications/subscription/add/", "icon": "fas fa-rss", "color": "primary"},
        {"name": "🔔 View All Notifications", "url": "/admin/notifications/notification/", "icon": "fas fa-list", "color": "secondary"},
    ],
    
    "stats_cards": [
        # Users stats
        {"title": "Total Users", "value": "{total_users}", "icon": "fas fa-users", "color": "primary"},
        {"title": "Active Users", "value": "{active_users}", "icon": "fas fa-user-check", "color": "success"},
        {"title": "Total Teams", "value": "{total_teams}", "icon": "fas fa-users-cog", "color": "info"},
        {"title": "Total Roles", "value": "{total_roles}", "icon": "fas fa-user-tag", "color": "warning"},
        {"title": "Permissions", "value": "{total_permissions}", "icon": "fas fa-key", "color": "danger"},
        
        # BI Roles stats
        {"title": "BI Analysts", "value": "{bi_analysts}", "icon": "fas fa-chart-line", "color": "info"},
        {"title": "BI Developers", "value": "{bi_developers}", "icon": "fas fa-code", "color": "primary"},
        {"title": "BI Consumers", "value": "{bi_consumers}", "icon": "fas fa-chart-pie", "color": "success"},
        {"title": "Dashboard Creators", "value": "{dashboard_creators}", "icon": "fas fa-chalkboard", "color": "warning"},
        
        # API & Security
        {"title": "API Users", "value": "{api_users}", "icon": "fas fa-plug", "color": "info"},
        {"title": "2FA Enabled", "value": "{two_factor_enabled}", "icon": "fas fa-mobile-alt", "color": "success"},
        {"title": "Verified Users", "value": "{verified_users}", "icon": "fas fa-check-circle", "color": "primary"},
        
        # Activities
        {"title": "Activities (24h)", "value": "{activities_24h}", "icon": "fas fa-history", "color": "secondary"},
        {"title": "Failed Logins (24h)", "value": "{failed_logins}", "icon": "fas fa-exclamation-triangle", "color": "danger"},
        
        # Core Configs
        {"title": "Configurations", "value": "{total_configs}", "icon": "fas fa-cogs", "color": "warning"},
        {"title": "Encrypted Configs", "value": "{encrypted_configs}", "icon": "fas fa-lock", "color": "danger"},
        
        # Data Sources
        {"title": "Data Sources", "value": "{total_sources}", "icon": "fas fa-database", "color": "primary"},
        {"title": "Active Sources", "value": "{active_sources}", "icon": "fas fa-check-circle", "color": "success"},
        {"title": "Error Sources", "value": "{error_sources}", "icon": "fas fa-exclamation-triangle", "color": "danger"},
        {"title": "Total Tables", "value": "{total_tables}", "icon": "fas fa-table", "color": "info"},
        {"title": "Total Queries", "value": "{total_queries}", "icon": "fas fa-code", "color": "secondary"},
        {"title": "Avg Quality Score", "value": "{avg_quality_score}", "icon": "fas fa-star", "color": "warning"},
        {"title": "Total Files", "value": "{total_files}", "icon": "fas fa-file-upload", "color": "purple"},
        {"title": "Power Queries", "value": "{power_queries_count}", "icon": "fas fa-chart-line", "color": "info"},
        {"title": "Star Schemas", "value": "{star_schemas_count}", "icon": "fas fa-star-of-life", "color": "success"},
        
        # ETL Engine
        {"title": "Total Pipelines", "value": "{total_pipelines}", "icon": "fas fa-code-branch", "color": "primary"},
        {"title": "Active Pipelines", "value": "{active_pipelines}", "icon": "fas fa-play-circle", "color": "success"},
        {"title": "Total Executions", "value": "{total_executions}", "icon": "fas fa-history", "color": "info"},
        {"title": "Success Rate", "value": "{pipeline_success_rate}%", "icon": "fas fa-chart-line", "color": "success"},
        {"title": "Avg Duration", "value": "{avg_duration}s", "icon": "fas fa-stopwatch", "color": "warning"},
        {"title": "Total Rows Processed", "value": "{total_rows_processed}", "icon": "fas fa-table", "color": "secondary"},
        {"title": "Transformations", "value": "{total_transformations}", "icon": "fas fa-filter", "color": "info"},
        
        # Data Warehouse
        {"title": "DW Schemas", "value": "{total_schemas}", "icon": "fas fa-draw-polygon", "color": "primary"},
        {"title": "DW Tables", "value": "{total_dw_tables}", "icon": "fas fa-table", "color": "success"},
        {"title": "Dimension Tables", "value": "{dimension_tables_count}", "icon": "fas fa-cube", "color": "info"},
        {"title": "Fact Tables", "value": "{fact_tables_count}", "icon": "fas fa-chart-simple", "color": "warning"},
        {"title": "Measures", "value": "{measures_count}", "icon": "fas fa-chart-line", "color": "danger"},
        {"title": "Aggregations", "value": "{aggregations_count}", "icon": "fas fa-chart-pie", "color": "secondary"},
        {"title": "DW Star Schemas", "value": "{dw_star_schemas_count}", "icon": "fas fa-star-of-life", "color": "purple"},
        {"title": "Total DW Rows", "value": "{total_dw_rows}", "icon": "fas fa-database", "color": "dark"},
        {"title": "DW Size (MB)", "value": "{dw_size_mb}", "icon": "fas fa-hdd", "color": "info"},
        
        # Star Schema
        {"title": "Dimensional Schemas", "value": "{total_dimensional_schemas}", "icon": "fas fa-cubes", "color": "primary"},
        {"title": "Custom Calculations", "value": "{total_calculations}", "icon": "fas fa-calculator", "color": "success"},
        {"title": "Dimension Hierarchies", "value": "{total_hierarchies}", "icon": "fas fa-sitemap", "color": "info"},
        {"title": "Fact Relationships", "value": "{total_fact_relationships}", "icon": "fas fa-link", "color": "warning"},
        {"title": "Galaxy Schemas", "value": "{total_galaxies}", "icon": "fas fa-globe", "color": "danger"},
        {"title": "Total Star Queries", "value": "{total_star_queries}", "icon": "fas fa-chart-line", "color": "secondary"},
        {"title": "Avg Query Time (ms)", "value": "{avg_star_query_time}", "icon": "fas fa-stopwatch", "color": "info"},
        
        # Visualizations
        {"title": "Dashboards", "value": "{total_dashboards}", "icon": "fas fa-tachometer-alt", "color": "primary"},
        {"title": "KPIs", "value": "{total_kpis}", "icon": "fas fa-chart-simple", "color": "success"},
        {"title": "Reports", "value": "{total_reports}", "icon": "fas fa-file-alt", "color": "info"},
        {"title": "Widgets", "value": "{total_widgets}", "icon": "fas fa-chart-pie", "color": "warning"},
        {"title": "Favorites", "value": "{total_favorites}", "icon": "fas fa-star", "color": "danger"},
        {"title": "Activities (24h)", "value": "{visualization_activities_24h}", "icon": "fas fa-history", "color": "secondary"},
        {"title": "Avg Dashboard Load (ms)", "value": "{avg_dashboard_load}", "icon": "fas fa-stopwatch", "color": "info"},
        
        # Notifications ← NOUVEAU
        {"title": "Total Notifications", "value": "{total_notifications}", "icon": "fas fa-envelope", "color": "primary"},
        {"title": "Unread", "value": "{unread_notifications}", "icon": "fas fa-envelope-open", "color": "warning"},
        {"title": "Alert Rules", "value": "{total_alert_rules}", "icon": "fas fa-exclamation-triangle", "color": "danger"},
        {"title": "Active Channels", "value": "{active_channels}", "icon": "fas fa-plug", "color": "success"},
        {"title": "Subscriptions", "value": "{total_subscriptions}", "icon": "fas fa-rss", "color": "info"},
        {"title": "Notifications (24h)", "value": "{notifications_24h}", "icon": "fas fa-history", "color": "secondary"},
    ],
    
    # ... (reste des sections recent_activities, recent_users, etc.)
    
    # Notifications sections ← NOUVEAU
    "recent_notifications": {
        "title": "🔔 Recent Notifications",
        "limit": 10,
        "model": "notifications.Notification",
        "fields": ["title", "notification_type", "priority", "recipient", "created_at"],
        "order_by": ["-created_at"],
    },
    
    "recent_alert_rules": {
        "title": "⚠️ Recent Alert Rules",
        "limit": 5,
        "model": "notifications.AlertRule",
        "fields": ["name", "kpi", "condition", "trigger_count", "is_enabled"],
        "order_by": ["-created_at"],
    },
    
    "recent_channels": {
        "title": "🔌 Recent Channels",
        "limit": 5,
        "model": "notifications.NotificationChannel",
        "fields": ["user", "channel", "address", "is_verified", "is_enabled"],
        "order_by": ["-created_at"],
    },
    
    "recent_subscriptions": {
        "title": "📡 Recent Subscriptions",
        "limit": 5,
        "model": "notifications.Subscription",
        "fields": ["user", "notification_type", "is_enabled", "created_at"],
        "order_by": ["-created_at"],
    },
    
    "charts": {
        # ... (charts existants)
        
        # Notifications charts ← NOUVEAU
        "notifications_by_type": {
            "title": "Notifications by Type",
            "type": "pie",
            "data_url": "/api/notifications/notifications/stats/",
        },
        "notifications_by_priority": {
            "title": "Notifications by Priority",
            "type": "pie",
            "data_url": "/api/notifications/notifications/stats/",
        },
        "notifications_timeline": {
            "title": "Notifications Timeline (Last 7 Days)",
            "type": "line",
            "data_url": "/api/notifications/notifications/stats/",
        },
        "alert_rules_by_condition": {
            "title": "Alert Rules by Condition",
            "type": "pie",
            "data_url": "/api/notifications/alerts/stats/",
        },
        "channels_by_type": {
            "title": "Notification Channels by Type",
            "type": "pie",
            "data_url": "/api/notifications/channels/stats/",
        },
        "subscriptions_by_type": {
            "title": "Subscriptions by Notification Type",
            "type": "pie",
            "data_url": "/api/notifications/subscriptions/stats/",
        },
    },
}

# ========================================================================
# FONCTIONS UTILITAIRES POUR LE DASHBOARD (Mise à jour avec Notifications)
# ========================================================================

def get_dashboard_stats():
    """
    Fonction pour récupérer les statistiques du dashboard (Core, Users, Data Sources, ETL Engine, Data Warehouse, Star Schema, Visualizations & Notifications)
    """
    from django.contrib.auth import get_user_model
    from apps.users.models import UserActivity, Team, Role, Permission
    from apps.core.models import Config
    from apps.data_sources.models import (
        DataSource, DataTable, DataQuery, DataSourceFile, 
        PowerQuery, StarSchema as DataSourceStarSchema, 
        DataSourceLog
    )
    from apps.etl_engine.models import ETLPipeline, ExecutionLog, Transformation
    from apps.data_warehouse.models import (
        DataWarehouseSchema, DataWarehouseTable, DimensionTable, 
        FactTable, Measure, AggregationTable, StarSchema,
        DataWarehouseLog, DataWarehouseMetric
    )
    from apps.star_schema.models import (
        DimensionalSchema, CustomCalculation, DimensionHierarchy,
        FactRelationship, GalaxySchema
    )
    from apps.visualizations.models import (
        Dashboard, KPI, Report, Widget, Favorite, VisualizationActivity
    )
    from apps.notifications.models import (
        Notification, NotificationChannel, Subscription, AlertRule
    )
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Avg, Sum, Q
    
    User = get_user_model()
    
    # ========================================================================
    # STATISTIQUES USERS
    # ========================================================================
    total_users = User.objects.count()
    active_users = User.objects.filter(status='active', is_active=True).count()
    total_teams = Team.objects.count()
    total_roles = Role.objects.count()
    total_permissions = Permission.objects.count()
    
    bi_analysts = User.objects.filter(role='bi_analyst').count()
    bi_developers = User.objects.filter(role='bi_developer').count()
    bi_consumers = User.objects.filter(role='bi_consumer').count()
    dashboard_creators = User.objects.filter(
        role__in=['superadmin', 'admin', 'bi_developer', 'bi_analyst']
    ).count()
    
    api_users = User.objects.filter(api_access_enabled=True).count()
    two_factor_enabled = User.objects.filter(two_factor_enabled=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    last_24h = timezone.now() - timedelta(hours=24)
    activities_24h = UserActivity.objects.filter(created_at__gte=last_24h).count()
    failed_logins = UserActivity.objects.filter(
        action='login',
        success=False,
        created_at__gte=last_24h
    ).count()
    
    # ========================================================================
    # STATISTIQUES CORE
    # ========================================================================
    total_configs = Config.objects.count()
    encrypted_configs = Config.objects.filter(is_encrypted=True).count()
    
    config_by_type = {}
    for config_type, _ in Config.CONFIG_TYPES:
        count = Config.objects.filter(config_type=config_type).count()
        if count > 0:
            config_by_type[config_type] = count
    
    # ========================================================================
    # STATISTIQUES DATA SOURCES
    # ========================================================================
    total_sources = DataSource.objects.count()
    active_sources = DataSource.objects.filter(status='active').count()
    error_sources = DataSource.objects.filter(status='error').count()
    
    total_tables = DataTable.objects.count()
    total_queries = DataQuery.objects.aggregate(Sum('execution_count'))['execution_count__sum'] or 0
    avg_quality_score = DataSource.objects.aggregate(Avg('data_quality_score'))['data_quality_score__avg'] or 0
    total_files = DataSourceFile.objects.count()
    power_queries_count = PowerQuery.objects.count()
    star_schemas_count = DataSourceStarSchema.objects.count()
    
    recent_logs = DataSourceLog.objects.filter(created_at__gte=last_24h).count()
    error_logs = DataSourceLog.objects.filter(level='error', created_at__gte=last_24h).count()
    
    sources_by_type = dict(
        DataSource.objects.values_list('source_type').annotate(count=Count('id'))
    )
    
    # ========================================================================
    # STATISTIQUES ETL ENGINE
    # ========================================================================
    total_pipelines = ETLPipeline.objects.count()
    active_pipelines = ETLPipeline.objects.filter(status='active').count()
    total_executions = ExecutionLog.objects.count()
    pipeline_success_rate = ExecutionLog.objects.filter(status='completed').count()
    if total_executions > 0:
        pipeline_success_rate = round((pipeline_success_rate / total_executions) * 100, 1)
    else:
        pipeline_success_rate = 100
    
    avg_duration = ExecutionLog.objects.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
    total_rows_processed = ExecutionLog.objects.aggregate(Sum('rows_written'))['rows_written__sum'] or 0
    total_transformations = Transformation.objects.count()
    
    recent_executions = ExecutionLog.objects.filter(started_at__gte=last_24h).count()
    failed_executions = ExecutionLog.objects.filter(status='failed', started_at__gte=last_24h).count()
    
    # ========================================================================
    # STATISTIQUES DATA WAREHOUSE
    # ========================================================================
    total_schemas = DataWarehouseSchema.objects.count()
    total_dw_tables = DataWarehouseTable.objects.count()
    dimension_tables_count = DimensionTable.objects.count()
    fact_tables_count = FactTable.objects.count()
    measures_count = Measure.objects.count()
    aggregations_count = AggregationTable.objects.count()
    dw_star_schemas_count = StarSchema.objects.count()
    
    total_dw_rows = DataWarehouseTable.objects.aggregate(Sum('row_count'))['row_count__sum'] or 0
    total_dw_size_bytes = DataWarehouseTable.objects.aggregate(Sum('size_bytes'))['size_bytes__sum'] or 0
    dw_size_mb = round(total_dw_size_bytes / (1024 * 1024), 2) if total_dw_size_bytes else 0
    
    dw_recent_logs = DataWarehouseLog.objects.filter(created_at__gte=last_24h).count()
    dw_error_logs = DataWarehouseLog.objects.filter(level='error', created_at__gte=last_24h).count()
    
    tables_by_type = dict(
        DataWarehouseTable.objects.values_list('table_type').annotate(count=Count('id'))
    )
    
    tables_by_status = dict(
        DataWarehouseTable.objects.values_list('status').annotate(count=Count('id'))
    )
    
    tables_refreshed_24h = DataWarehouseTable.objects.filter(
        last_refresh__gte=last_24h
    ).count()
    
    avg_query_time = DataWarehouseMetric.objects.aggregate(Avg('query_time_ms'))['query_time_ms__avg'] or 0
    total_metrics = DataWarehouseMetric.objects.count()
    
    # ========================================================================
    # STATISTIQUES STAR SCHEMA
    # ========================================================================
    total_dimensional_schemas = DimensionalSchema.objects.count()
    total_calculations = CustomCalculation.objects.count()
    total_hierarchies = DimensionHierarchy.objects.count()
    total_fact_relationships = FactRelationship.objects.count()
    total_galaxies = GalaxySchema.objects.count()
    
    total_star_queries = DimensionalSchema.objects.aggregate(Sum('query_count'))['query_count__sum'] or 0
    avg_star_query_time = DimensionalSchema.objects.aggregate(Avg('avg_query_time_ms'))['avg_query_time_ms__avg'] or 0
    
    active_dimensional_schemas = DimensionalSchema.objects.filter(status='active').count()
    star_schemas_by_type = dict(
        DimensionalSchema.objects.values_list('schema_type').annotate(count=Count('id'))
    )
    
    # ========================================================================
    # STATISTIQUES VISUALIZATIONS
    # ========================================================================
    total_dashboards = Dashboard.objects.count()
    total_kpis = KPI.objects.count()
    total_reports = Report.objects.count()
    total_widgets = Widget.objects.count()
    total_favorites = Favorite.objects.count()
    
    visualization_activities_24h = VisualizationActivity.objects.filter(created_at__gte=last_24h).count()
    avg_dashboard_load = Dashboard.objects.aggregate(Avg('avg_load_time_ms'))['avg_load_time_ms__avg'] or 0
    
    active_dashboards = Dashboard.objects.filter(status='published').count()
    active_kpis = KPI.objects.filter(is_active=True).count()
    
    dashboards_by_type = dict(
        Dashboard.objects.values_list('dashboard_type').annotate(count=Count('id'))
    )
    
    kpis_by_type = dict(
        KPI.objects.values_list('kpi_type').annotate(count=Count('id'))
    )
    
    # ========================================================================
    # STATISTIQUES NOTIFICATIONS ← NOUVEAU
    # ========================================================================
    total_notifications = Notification.objects.count()
    unread_notifications = Notification.objects.filter(read_at__isnull=True).count()
    total_alert_rules = AlertRule.objects.count()
    active_alert_rules = AlertRule.objects.filter(is_enabled=True).count()
    total_channels = NotificationChannel.objects.count()
    active_channels = NotificationChannel.objects.filter(is_enabled=True, is_verified=True).count()
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(is_enabled=True).count()
    notifications_24h = Notification.objects.filter(created_at__gte=last_24h).count()
    
    notifications_by_type = dict(
        Notification.objects.values_list('notification_type').annotate(count=Count('id'))
    )
    
    notifications_by_priority = dict(
        Notification.objects.values_list('priority').annotate(count=Count('id'))
    )
    
    alert_rules_by_condition = dict(
        AlertRule.objects.values_list('condition').annotate(count=Count('id'))
    )
    
    channels_by_type = dict(
        NotificationChannel.objects.values_list('channel').annotate(count=Count('id'))
    )
    
    subscriptions_by_type = dict(
        Subscription.objects.values_list('notification_type').annotate(count=Count('id'))
    )
    
    return {
        # Users
        'total_users': total_users,
        'active_users': active_users,
        'total_teams': total_teams,
        'total_roles': total_roles,
        'total_permissions': total_permissions,
        'bi_analysts': bi_analysts,
        'bi_developers': bi_developers,
        'bi_consumers': bi_consumers,
        'dashboard_creators': dashboard_creators,
        'api_users': api_users,
        'two_factor_enabled': two_factor_enabled,
        'verified_users': verified_users,
        'activities_24h': activities_24h,
        'failed_logins': failed_logins,
        
        # Core
        'total_configs': total_configs,
        'encrypted_configs': encrypted_configs,
        'config_by_type': config_by_type,
        
        # Data Sources
        'total_sources': total_sources,
        'active_sources': active_sources,
        'error_sources': error_sources,
        'total_tables': total_tables,
        'total_queries': total_queries,
        'avg_quality_score': round(avg_quality_score, 1),
        'total_files': total_files,
        'power_queries_count': power_queries_count,
        'star_schemas_count': star_schemas_count,
        'recent_logs': recent_logs,
        'error_logs': error_logs,
        'sources_by_type': sources_by_type,
        
        # ETL Engine
        'total_pipelines': total_pipelines,
        'active_pipelines': active_pipelines,
        'total_executions': total_executions,
        'pipeline_success_rate': pipeline_success_rate,
        'avg_duration': round(avg_duration, 1),
        'total_rows_processed': total_rows_processed,
        'total_transformations': total_transformations,
        'recent_executions': recent_executions,
        'failed_executions': failed_executions,
        
        # Data Warehouse
        'total_schemas': total_schemas,
        'total_dw_tables': total_dw_tables,
        'dimension_tables_count': dimension_tables_count,
        'fact_tables_count': fact_tables_count,
        'measures_count': measures_count,
        'aggregations_count': aggregations_count,
        'dw_star_schemas_count': dw_star_schemas_count,
        'total_dw_rows': total_dw_rows,
        'dw_size_mb': dw_size_mb,
        'dw_recent_logs': dw_recent_logs,
        'dw_error_logs': dw_error_logs,
        'tables_by_type': tables_by_type,
        'tables_by_status': tables_by_status,
        'tables_refreshed_24h': tables_refreshed_24h,
        'avg_query_time_ms': round(avg_query_time, 2),
        'total_metrics': total_metrics,
        
        # Star Schema
        'total_dimensional_schemas': total_dimensional_schemas,
        'total_calculations': total_calculations,
        'total_hierarchies': total_hierarchies,
        'total_fact_relationships': total_fact_relationships,
        'total_galaxies': total_galaxies,
        'total_star_queries': total_star_queries,
        'avg_star_query_time': round(avg_star_query_time, 2),
        'active_dimensional_schemas': active_dimensional_schemas,
        'star_schemas_by_type': star_schemas_by_type,
        
        # Visualizations
        'total_dashboards': total_dashboards,
        'total_kpis': total_kpis,
        'total_reports': total_reports,
        'total_widgets': total_widgets,
        'total_favorites': total_favorites,
        'visualization_activities_24h': visualization_activities_24h,
        'avg_dashboard_load': round(avg_dashboard_load, 2),
        'active_dashboards': active_dashboards,
        'active_kpis': active_kpis,
        'dashboards_by_type': dashboards_by_type,
        'kpis_by_type': kpis_by_type,
        
        # Notifications ← NOUVEAU
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'total_alert_rules': total_alert_rules,
        'active_alert_rules': active_alert_rules,
        'total_channels': total_channels,
        'active_channels': active_channels,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'notifications_24h': notifications_24h,
        'notifications_by_type': notifications_by_type,
        'notifications_by_priority': notifications_by_priority,
        'alert_rules_by_condition': alert_rules_by_condition,
        'channels_by_type': channels_by_type,
        'subscriptions_by_type': subscriptions_by_type,
    }