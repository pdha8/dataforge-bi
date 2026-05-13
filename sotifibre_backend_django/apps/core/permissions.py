# apps/core/permissions.py
"""
Custom Permission Classes for Sotifibre BI Platform
"""
from rest_framework import permissions


# ========================================================================
# PERMISSIONS DE BASE
# ========================================================================

class IsSuperAdmin(permissions.BasePermission):
    """Only superadmins can access"""
    message = "👑 Seuls les super-administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'is_superadmin', False))


class IsAdmin(permissions.BasePermission):
    """Superadmins and admins can access"""
    message = "⚙️ Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'is_admin', False))


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admins can edit, others can only read"""
    message = "✏️ Vous n'avez pas les droits de modification."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return getattr(request.user, 'is_admin', False)


class IsOwnerOrAdmin(permissions.BasePermission):
    """User is owner of object or admin"""
    message = "🔒 Vous n'êtes pas le propriétaire de cette ressource."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if getattr(request.user, 'is_admin', False):
            return True
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False

# ========================================================================
# COMBINED PERMISSIONS
# ========================================================================

class IsActiveUser(permissions.BasePermission):
    """User account must be active"""
    message = "⏸️ Votre compte n'est pas actif."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.status == 'active')


class HasAPIAccess(permissions.BasePermission):
    """User has API access enabled"""
    message = "🔑 Votre accès API est désactivé."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.api_access_enabled)


class IsVerified(permissions.BasePermission):
    """User account must be verified"""
    message = "✅ Votre compte doit être vérifié d'abord."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.is_verified)


class IsAdminAndActive(permissions.BasePermission):
    """Must be admin and have active account"""
    message = "⚙️ Vous devez être administrateur avec un compte actif."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'is_admin', False) and 
                request.user.status == 'active')


class HasPermissionCode(permissions.BasePermission):
    """Check if user has specific permission code"""
    required_permission = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superadmins have all permissions
        if getattr(request.user, 'is_superadmin', False):
            return True
        
        # Check user's role permissions
        from apps.users.models import Role
        try:
            user_role = Role.objects.get(name=request.user.role)
            permission_code = self.required_permission or getattr(view, 'required_permission', None)
            return user_role.has_permission(permission_code) if permission_code else False
        except Role.DoesNotExist:
            return False
        
# ========================================================================
# PERMISSIONS SOTIFIBRE SPÉCIFIQUES
# ========================================================================

class CanManageDataSources(permissions.BasePermission):
    """Permission to manage data sources"""
    message = "🗄️ Vous n'avez pas la permission de gérer les sources de données."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_manage_data_sources', False))


class CanViewDataSources(permissions.BasePermission):
    """Permission to view data sources"""
    message = "👀 Vous n'avez pas la permission de voir les sources de données."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_data_sources', True))


class CanManageETL(permissions.BasePermission):
    """Permission to manage ETL pipelines"""
    message = "🔄 Vous n'avez pas la permission de gérer les pipelines ETL."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_manage_etl', False))


class CanViewETL(permissions.BasePermission):
    """Permission to view ETL pipelines"""
    message = "👀 Vous n'avez pas la permission de voir les pipelines ETL."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_etl', True))


class CanManageDashboards(permissions.BasePermission):
    """Permission to manage dashboards"""
    message = "📊 Vous n'avez pas la permission de gérer les tableaux de bord."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_manage_dashboards', False))


class CanViewDashboards(permissions.BasePermission):
    """Permission to view dashboards"""
    message = "👀 Vous n'avez pas la permission de voir les tableaux de bord."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_dashboards', True))


class CanCreateDashboards(permissions.BasePermission):
    """Permission to create dashboards"""
    message = "📝 Vous n'avez pas la permission de créer des tableaux de bord."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_create_dashboards', False))


class CanShareDashboards(permissions.BasePermission):
    """Permission to share dashboards"""
    message = "🔗 Vous n'avez pas la permission de partager des tableaux de bord."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_share_dashboards', False))


class CanExportData(permissions.BasePermission):
    """Permission to export data"""
    message = "📤 Vous n'avez pas la permission d'exporter les données."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_export_data', False))


class CanScheduleReports(permissions.BasePermission):
    """Permission to schedule reports"""
    message = "📅 Vous n'avez pas la permission de planifier des rapports."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_schedule_reports', False))


class CanManageKPIs(permissions.BasePermission):
    """Permission to manage KPIs"""
    message = "🎯 Vous n'avez pas la permission de gérer les KPIs."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_manage_kpis', False))


class CanViewKPIs(permissions.BasePermission):
    """Permission to view KPIs"""
    message = "👀 Vous n'avez pas la permission de voir les KPIs."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_kpis', True))


# ========================================================================
# PERMISSIONS COMBINÉES BI
# ========================================================================

class IsBIAnalyst(permissions.BasePermission):
    """User is a BI analyst"""
    message = "📊 Seuls les analystes BI peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'role') == 'bi_analyst')


class IsBIDeveloper(permissions.BasePermission):
    """User is a BI developer"""
    message = "💻 Seuls les développeurs BI peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'role') == 'bi_developer')


class IsBIConsumer(permissions.BasePermission):
    """User is a BI consumer (read-only)"""
    message = "📱 Les consommateurs BI ont un accès en lecture seule."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return getattr(request.user, 'role') not in ['bi_consumer']


class HasFullBIAccess(permissions.BasePermission):
    """User has full BI access"""
    message = "🔒 Accès BI complet requis."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'bi_access_level') in ['admin', 'developer'])