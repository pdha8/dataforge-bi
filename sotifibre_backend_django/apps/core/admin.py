# apps/core/admin.py
"""
Core Admin - Configuration de la plateforme Sotifibre BI
"""
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
import json

from .models import Config


# ============================================================================
# RESSOURCE POUR IMPORT/EXPORT
# ============================================================================

class ConfigResource(resources.ModelResource):
    """Resource pour l'import/export des configurations Sotifibre"""
    
    class Meta:
        model = Config
        fields = ('id', 'key', 'config_type', 'is_encrypted', 'created_at', 'updated_at')
        export_order = fields


# ============================================================================
# ADMIN DE LA CONFIGURATION
# ============================================================================

@admin.register(Config)
class ConfigAdmin(ImportExportModelAdmin):
    """
    Administration des configurations globales Sotifibre BI
    """
    resource_class = ConfigResource
    
    # Liste
    list_display = [
        'key_display', 'config_type_badge', 'value_preview', 
        'encrypted_indicator', 'created_at'
    ]
    list_display_links = ['key_display']
    
    # Filtres
    list_filter = ['config_type', 'is_encrypted', 'created_at']
    
    # Recherche
    search_fields = ['key', 'description', 'value']
    
    # Organisation
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    # Champs
    fieldsets = (
        ('⚙️ Configuration BI', {
            'fields': ('key', 'config_type', 'description')
        }),
        ('📊 Valeur', {
            'fields': ('value',),
            'description': '''
                <div class="alert alert-info">
                    <strong>Format JSON:</strong> La valeur doit être au format JSON valide.
                    <br><strong>Exemples BI:</strong> 
                    <code>{"refresh_frequency": "hourly", "cache_ttl": 3600}</code>, 
                    <code>["postgresql", "mysql", "mongodb"]</code>, 
                    <code>42</code>, 
                    <code>"dashboard_default_theme"</code>
                </div>
            '''
        }),
        ('🔒 Sécurité', {
            'fields': ('is_encrypted',),
            'classes': ('collapse',)
        }),
        ('📈 Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'value_formatted']
    
    # ========================================================================
    # MÉTHODES D'AFFICHAGE
    # ========================================================================
    
    def key_display(self, obj):
        """Affiche la clé avec un formatage spécial selon le type BI"""
        icons = {
            # Types BI
            'general': '⚙️',
            'security': '🛡️',
            'data_sources': '🗄️',
            'etl': '🔄',
            'warehouse': '🏢',
            'visualization': '📊',
            'dashboard': '📈',
            'kpi': '🎯',
            'notifications': '🔔',
            'exports': '📤',
            'integrations': '🔌',
            'cache': '⚡',
            'performance': '⏱️',
            'licensing': '📜',
        }
        icon = icons.get(obj.config_type, '📊')
        return format_html(
            '<strong>{} {}</strong><br><small class="text-muted">{}</small>',
            icon, obj.key, obj.description[:50] + '...' if obj.description else ''
        )
    key_display.short_description = 'Configuration BI'
    key_display.admin_order_field = 'key'
    
    def config_type_badge(self, obj):
        """Badge pour le type de configuration avec couleurs adaptées à Sotifibre"""
        colors = {
            # Types BI
            'general': 'secondary',
            'security': 'danger',
            'data_sources': 'info',
            'etl': 'primary',
            'warehouse': 'success',
            'visualization': 'purple',
            'dashboard': 'warning',
            'kpi': 'danger',
            'notifications': 'success',
            'exports': 'info',
            'integrations': 'dark',
            'cache': 'primary',
            'performance': 'warning',
            'licensing': 'secondary',
        }
        color = colors.get(obj.config_type, 'secondary')
        
        # Traduction des types en français
        type_labels = {
            'general': 'Général',
            'security': 'Sécurité',
            'data_sources': 'Sources de données',
            'etl': 'ETL',
            'warehouse': 'Entrepôt',
            'visualization': 'Visualisation',
            'dashboard': 'Tableaux de bord',
            'kpi': 'KPIs',
            'notifications': 'Notifications',
            'exports': 'Exports',
            'integrations': 'Intégrations',
            'cache': 'Cache',
            'performance': 'Performance',
            'licensing': 'Licence',
        }
        label = type_labels.get(obj.config_type, obj.get_config_type_display())
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, label
        )
    config_type_badge.short_description = 'Type BI'
    config_type_badge.admin_order_field = 'config_type'
    
    def value_preview(self, obj):
        """Aperçu de la valeur avec formatage BI"""
        try:
            if isinstance(obj.value, dict):
                # Pour les dictionnaires, afficher les clés principales
                keys = list(obj.value.keys())
                if len(keys) > 3:
                    preview = ', '.join(keys[:3]) + f' +{len(keys)-3}'
                else:
                    preview = ', '.join(keys)
                return f"{{ {preview} }}"
            elif isinstance(obj.value, list):
                return f"[{len(obj.value)} éléments]"
            else:
                value_str = str(obj.value)
                if len(value_str) > 50:
                    return value_str[:50] + '...'
                return value_str
        except:
            return '⚠️ Erreur de format'
    value_preview.short_description = 'Valeur'
    
    def encrypted_indicator(self, obj):
        """Indicateur de chiffrement"""
        if obj.is_encrypted:
            return format_html('<span class="badge bg-warning" title="Donnée chiffrée">🔒 Chiffré</span>')
        return format_html('<span class="badge bg-success" title="Donnée en clair">🔓 Clair</span>')
    encrypted_indicator.short_description = 'Sécurité'
    
    def value_formatted(self, obj):
        """Affiche la valeur formatée en JSON avec style BI"""
        try:
            if isinstance(obj.value, (dict, list)):
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px;">{}</pre>',
                    json.dumps(obj.value, indent=2, ensure_ascii=False)
                )
            else:
                return format_html(
                    '<code>{}</code>',
                    obj.value
                )
        except:
            return format_html(
                '<span class="text-danger">Erreur de format JSON</span>'
            )
    value_formatted.short_description = 'Valeur (formatée)'
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def save_model(self, request, obj, form, change):
        """Validation avant sauvegarde avec règles BI"""
        try:
            # S'assurer que la valeur est un JSON valide
            if isinstance(obj.value, str):
                try:
                    obj.value = json.loads(obj.value)
                except json.JSONDecodeError:
                    pass
            
            # Validation spécifique BI selon le type
            if obj.config_type == 'data_sources' and isinstance(obj.value, dict):
                required_keys = ['connection_timeout', 'max_connections', 'pool_size']
                for key in required_keys:
                    if key not in obj.value:
                        self.message_user(
                            request,
                            f'⚠️ La configuration des sources de données devrait contenir "{key}"',
                            messages.WARNING
                        )
            
            elif obj.config_type == 'visualization' and isinstance(obj.value, dict):
                if 'default_chart_type' in obj.value:
                    valid_charts = ['bar', 'line', 'pie', 'area', 'scatter', 'heatmap']
                    if obj.value['default_chart_type'] not in valid_charts:
                        raise ValueError(f"Type de graphique invalide")
            
            elif obj.config_type == 'cache' and isinstance(obj.value, dict):
                if 'ttl' in obj.value and not isinstance(obj.value['ttl'], (int, float)):
                    raise ValueError("Le TTL du cache doit être un nombre")
                if obj.value.get('ttl', 0) < 0:
                    raise ValueError("Le TTL du cache ne peut pas être négatif")
            
            super().save_model(request, obj, form, change)
            
            action = 'modifiée' if change else 'créée'
            self.message_user(
                request, 
                f'✅ Configuration BI "{obj.key}" {action} avec succès.',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'❌ Erreur: {str(e)}',
                messages.ERROR
            )
    
    # ========================================================================
    # ACTIONS PERSONNALISÉES
    # ========================================================================
    
    actions = ['duplicate_config', 'export_selected', 'toggle_encryption', 'validate_configs']
    
    def duplicate_config(self, request, queryset):
        """Duplique une configuration"""
        for config in queryset:
            new_key = f"{config.key}_copie"
            count = 1
            while Config.objects.filter(key=new_key).exists():
                count += 1
                new_key = f"{config.key}_copie_{count}"
            
            Config.objects.create(
                key=new_key,
                value=config.value,
                description=f"Copie de {config.key}",
                config_type=config.config_type,
                is_encrypted=config.is_encrypted
            )
        
        self.message_user(
            request,
            f'✅ {queryset.count()} configuration(s) BI dupliquée(s).',
            messages.SUCCESS
        )
    duplicate_config.short_description = "📋 Dupliquer la sélection BI"
    
    def export_selected(self, request, queryset):
        """Export JSON des configurations sélectionnées"""
        from django.http import HttpResponse
        
        data = []
        for config in queryset:
            data.append({
                'key': config.key,
                'value': config.value,
                'description': config.description,
                'config_type': config.config_type,
                'config_type_display': config.get_config_type_display(),
                'is_encrypted': config.is_encrypted,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2, default=str, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="sotifibre_configurations.json"'
        return response
    export_selected.short_description = "📤 Exporter la sélection BI"
    
    def toggle_encryption(self, request, queryset):
        """Active/désactive le chiffrement"""
        count = 0
        for config in queryset:
            config.is_encrypted = not config.is_encrypted
            config.save()
            count += 1
        
        self.message_user(
            request,
            f'🔄 Statut de chiffrement modifié pour {count} configuration(s).',
            messages.SUCCESS
        )
    toggle_encryption.short_description = "🔄 Basculer chiffrement"
    
    def validate_configs(self, request, queryset):
        """Valide les configurations sélectionnées"""
        errors = []
        warnings = []
        
        for config in queryset:
            if config.config_type == 'data_sources' and isinstance(config.value, dict):
                if 'connection_timeout' in config.value and not isinstance(config.value['connection_timeout'], int):
                    errors.append(f"{config.key}: connection_timeout doit être un entier")
            
            elif config.config_type == 'visualization' and isinstance(config.value, dict):
                if 'default_chart_type' in config.value:
                    valid_charts = ['bar', 'line', 'pie', 'area', 'scatter', 'heatmap']
                    if config.value['default_chart_type'] not in valid_charts:
                        errors.append(f"{config.key}: default_chart_type invalide")
            
            elif config.config_type == 'cache' and isinstance(config.value, dict):
                if 'ttl' in config.value:
                    if not isinstance(config.value['ttl'], (int, float)) or config.value['ttl'] < 0:
                        errors.append(f"{config.key}: ttl doit être un nombre positif")
        
        if errors:
            self.message_user(
                request,
                f'❌ Erreurs:\n' + '\n'.join(errors),
                messages.ERROR
            )
        elif warnings:
            self.message_user(
                request,
                f'⚠️ Avertissements:\n' + '\n'.join(warnings),
                messages.WARNING
            )
        else:
            self.message_user(
                request,
                f'✅ Toutes les configurations sont valides.',
                messages.SUCCESS
            )
    validate_configs.short_description = "✅ Valider la sélection"
    
    # ========================================================================
    # PERMISSIONS
    # ========================================================================
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append('key')
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        critical_keys = [
            'platform.version', 
            'platform.secret_key', 
            'database.config',
            'security.master_key',
            'api.secret',
            'encryption.key',
            'bi.default_theme',
            'bi.license_key',
            'warehouse.connection',
            'cache.redis_config',
        ]
        if obj and obj.key in critical_keys:
            return False
        return super().has_delete_permission(request, obj)


# ============================================================================
# CONFIGURATION DU DASHBOARD CORE
# ============================================================================

class CoreDashboard:
    """
    Statistiques pour le dashboard core Sotifibre
    """
    
    @staticmethod
    def get_stats():
        """Récupère les statistiques des configurations BI"""
        from django.utils import timezone
        from datetime import timedelta
        
        total_configs = Config.objects.count()
        
        configs_by_type = {}
        type_labels = {
            'general': 'Général',
            'security': 'Sécurité',
            'data_sources': 'Sources de données',
            'etl': 'ETL',
            'warehouse': 'Entrepôt',
            'visualization': 'Visualisation',
            'dashboard': 'Tableaux de bord',
            'kpi': 'KPIs',
            'notifications': 'Notifications',
            'exports': 'Exports',
            'integrations': 'Intégrations',
            'cache': 'Cache',
            'performance': 'Performance',
            'licensing': 'Licence',
        }
        
        for config_type, _ in Config.CONFIG_TYPES:
            count = Config.objects.filter(config_type=config_type).count()
            if count > 0:
                label = type_labels.get(config_type, config_type)
                configs_by_type[label] = count
        
        encrypted_count = Config.objects.filter(is_encrypted=True).count()
        
        return {
            'total_configs': total_configs,
            'total_configs_display': f'{total_configs} configuration(s) BI',
            'configs_by_type': configs_by_type,
            'encrypted_count': encrypted_count,
            'encrypted_percentage': round((encrypted_count / total_configs * 100) if total_configs > 0 else 0, 1),
        }


# Configuration de l'interface d'administration
admin.site.site_header = "Sotifibre BI - Administration"
admin.site.site_title = "Sotifibre Admin"
admin.site.index_title = "📊 Tableau de bord Sotifibre BI"