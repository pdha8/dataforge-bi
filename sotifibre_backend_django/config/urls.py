"""
IOTShield Platform URLs - Ultra Professional
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# drf-yasg schema
schema_view_yasg = get_schema_view(
    openapi.Info(
        title="Sotifibre BI Platform API",
        default_version='v1',
        description="Plateforme d'analyse de données et Business Intelligence avancée.",
        contact=openapi.Contact(email="sotifibre@sotetel.tn"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    # JWT Authentication
    path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/jwt/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # ========================================================================
    # API DOCUMENTATION
    # ========================================================================
    
    # drf-spectacular (OpenAPI 3.0) - PREFERRED
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # drf-yasg (Swagger 2.0) - Legacy
    path('api/docs/', schema_view_yasg.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view_yasg.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/swagger.json/', schema_view_yasg.without_ui(cache_timeout=0), name='schema-json'),

    # ========================================================================
    # CORE APPLICATIONS
    # ========================================================================
    
    # Users App - Gestion des utilisateurs BI
    path('api/users/', include('apps.users.urls')),
    
    # ========================================================================
    # BI APPLICATIONS
    # ========================================================================
    
     # Data Sources App - Gestion des sources de données
    path('api/data-sources/', include('apps.data_sources.urls')),
    
    # ETL Engine App - Moteur ETL ← AJOUTER CORRECTEMENT
    path('api/etl/', include('apps.etl_engine.urls')),
    
    # Data Warehouse App - Entrepôt de données
    path('api/data-warehouse/', include('apps.data_warehouse.urls')),
    
    # Star Schema App - Modélisation dimensionnelle avancée
    path('api/star-schema/', include('apps.star_schema.urls')),
    
    # Visualizations App - Tableaux de bord, KPIs et rapports
    path('api/visualizations/', include('apps.visualizations.urls')),

    # Notifications App - Alertes et communications BI ← NOUVEAU
    path('api/notifications/', include('apps.notifications.urls')),

    # ML Analytics App - Analyse et modeles ML
    path('api/ml-analytics/', include('apps.ml_analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
