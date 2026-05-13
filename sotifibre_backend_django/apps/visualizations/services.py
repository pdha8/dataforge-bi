# apps/visualizations/services.py
"""
Services pour l'application visualizations
"""
import json
import pandas as pd
from io import BytesIO
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse

from apps.core.utils import Timer
from apps.star_schema.services import DimensionalSchemaService
from apps.data_warehouse.services import DataWarehouseService


class DashboardService:
    """Service pour la gestion des tableaux de bord"""
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
    
    def render(self, filters=None):
        """
        Rendu complet du tableau de bord
        """
        result = {
            'id': str(self.dashboard.id),
            'name': self.dashboard.name,
            'description': self.dashboard.description,
            'layout': self.dashboard.layout,
            'theme': self.dashboard.theme,
            'widgets': [],
            'kpis': []
        }
        
        # Rendre les widgets
        for widget in self.dashboard.widgets.filter(is_enabled=True):
            try:
                widget_data = self._render_widget(widget, filters)
                result['widgets'].append(widget_data)
            except Exception as e:
                result['widgets'].append({
                    'id': str(widget.id),
                    'name': widget.name,
                    'error': str(e)
                })
        
        # Rendre les KPIs
        for kpi in self.dashboard.kpis.filter(is_active=True):
            try:
                kpi_data = self._render_kpi(kpi, filters)
                result['kpis'].append(kpi_data)
            except Exception as e:
                result['kpis'].append({
                    'id': str(kpi.id),
                    'name': kpi.name,
                    'error': str(e)
                })
        
        return result
    
    def _render_widget(self, widget, filters=None):
        """Rendu d'un widget"""
        service = WidgetDataService(widget)
        data = service.fetch_data(filters)
        
        render_service = WidgetRenderService(widget)
        rendered = render_service.render(data)
        
        return {
            'id': str(widget.id),
            'name': widget.name,
            'type': widget.widget_type,
            'position': widget.position,
            'config': widget.config,
            'data': rendered,
            'style': widget.style
        }
    
    def _render_kpi(self, kpi, filters=None):
        """Rendu d'un KPI"""
        service = KPIService(kpi)
        data = service.calculate(filters)
        
        return {
            'id': str(kpi.id),
            'name': kpi.name,
            'type': kpi.kpi_type,
            'value': data.get('value'),
            'previous_value': data.get('previous_value'),
            'trend': data.get('trend'),
            'trend_percentage': data.get('trend_percentage'),
            'status': kpi.get_status(),
            'status_color': kpi.get_status_color(),
            'status_icon': kpi.get_status_icon(),
            'target': kpi.target_value,
            'format': kpi.format_string,
            'unit': kpi.unit
        }


class WidgetDataService:
    """Service pour la récupération des données de widget"""
    
    def __init__(self, widget):
        self.widget = widget
    
    def fetch_data(self, filters=None):
        """
        Récupère les données pour le widget
        """
        cache_key = f"widget_data_{self.widget.id}_{hash(str(filters))}"
        
        if self.widget.cache_enabled:
            cached = cache.get(cache_key)
            if cached:
                return cached
        
        if self.widget.dimensional_schema:
            service = DimensionalSchemaService(self.widget.dimensional_schema)
            result = service.execute(filters)
            data = result.get('data', [])
        else:
            data = []
        
        if self.widget.cache_enabled:
            cache.set(cache_key, data, self.widget.cache_ttl_seconds)
            self.widget.cached_data = data
            self.widget.cached_at = timezone.now()
            self.widget.save(update_fields=['cached_data', 'cached_at'])
        
        return data


class WidgetRenderService:
    """Service pour le rendu des widgets"""
    
    def __init__(self, widget):
        self.widget = widget
    
    def render(self, data=None):
        """
        Rendu du widget selon son type
        """
        if self.widget.widget_type == 'chart':
            return self._render_chart(data)
        elif self.widget.widget_type == 'metric':
            return self._render_metric(data)
        elif self.widget.widget_type == 'table':
            return self._render_table(data)
        elif self.widget.widget_type == 'text':
            return self._render_text()
        else:
            return self._render_default(data)
    
    def _render_chart(self, data):
        """Rendu d'un graphique"""
        config = self.widget.config
        chart_type = config.get('type', 'bar')
        
        return {
            'type': 'chart',
            'chart_type': chart_type,
            'config': config,
            'data': data
        }
    
    def _render_metric(self, data):
        """Rendu d'une métrique"""
        if data and len(data) > 0:
            value = data[0].get('value', 0)
        else:
            value = 0
        
        return {
            'type': 'metric',
            'value': value,
            'format': self.widget.config.get('format', '#,##0'),
            'unit': self.widget.config.get('unit', '')
        }
    
    def _render_table(self, data):
        """Rendu d'un tableau"""
        columns = []
        if data and len(data) > 0:
            columns = list(data[0].keys())
        
        return {
            'type': 'table',
            'columns': columns,
            'data': data
        }
    
    def _render_text(self):
        """Rendu de texte"""
        return {
            'type': 'text',
            'content': self.widget.config.get('content', '')
        }
    
    def _render_default(self, data):
        """Rendu par défaut"""
        return {
            'type': 'default',
            'data': data
        }


class KPIService:
    """Service pour le calcul des KPIs"""
    
    def __init__(self, kpi):
        self.kpi = kpi
    
    def calculate(self, filters=None):
        """
        Calcule la valeur du KPI
        """
        timer = Timer().start()
        
        try:
            if self.kpi.formula:
                # Calcul personnalisé
                value = self._calculate_formula(filters)
            elif self.kpi.measure:
                # Calcul basé sur une mesure
                value = self._calculate_measure(filters)
            else:
                value = 0
            
            previous_value = self.kpi.previous_value
            trend = None
            trend_percentage = None
            
            if previous_value is not None and previous_value != 0:
                trend_percentage = ((value - previous_value) / previous_value) * 100
                trend = 'up' if trend_percentage > 0 else 'down' if trend_percentage < 0 else 'stable'
            
            # Mettre à jour le KPI
            self.kpi.current_value = value
            self.kpi.previous_value = self.kpi.current_value
            self.kpi.trend_percentage = trend_percentage
            self.kpi.last_calculated = timezone.now()
            self.kpi.save(update_fields=['current_value', 'previous_value', 'trend_percentage', 'last_calculated'])
            
            timer.stop()
            
            return {
                'success': True,
                'value': value,
                'previous_value': previous_value,
                'trend': trend,
                'trend_percentage': trend_percentage,
                'execution_time_ms': timer.duration_ms()
            }
            
        except Exception as e:
            timer.stop()
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': timer.duration_ms()
            }
    
    def _calculate_formula(self, filters=None):
        """Calcul via formule personnalisée"""
        # À implémenter avec un évaluateur sécurisé
        return 0
    
    def _calculate_measure(self, filters=None):
        """Calcul via mesure"""
        if not self.kpi.dimensional_schema or not self.kpi.measure:
            return 0
        
        service = DimensionalSchemaService(self.kpi.dimensional_schema)
        result = service.execute(filters)
        
        if result['success'] and result['data']:
            agg_func = self.kpi.aggregation.upper()
            column = self.kpi.measure.column
            
            if agg_func == 'SUM':
                return sum(row.get(column, 0) for row in result['data'])
            elif agg_func == 'AVG':
                values = [row.get(column, 0) for row in result['data']]
                return sum(values) / len(values) if values else 0
            elif agg_func == 'COUNT':
                return len(result['data'])
            elif agg_func == 'MIN':
                return min(row.get(column, 0) for row in result['data'])
            elif agg_func == 'MAX':
                return max(row.get(column, 0) for row in result['data'])
        
        return 0


class ReportGenerationService:
    """Service pour la génération de rapports"""
    
    def __init__(self, report):
        self.report = report
    
    def generate(self, user=None):
        """
        Génère le rapport
        """
        timer = Timer().start()
        
        try:
            # Récupérer les données du dashboard
            dashboard_service = DashboardService(self.report.dashboard)
            data = dashboard_service.render(self.report.filters)
            
            # Générer selon le format
            if self.report.format == 'pdf':
                result = self._generate_pdf(data)
            elif self.report.format == 'csv':
                result = self._generate_csv(data)
            elif self.report.format == 'excel':
                result = self._generate_excel(data)
            elif self.report.format == 'json':
                result = self._generate_json(data)
            elif self.report.format == 'html':
                result = self._generate_html(data)
            else:
                result = self._generate_json(data)
            
            # Mettre à jour les statistiques
            self.report.last_generated = timezone.now()
            self.report.last_generated_by = user
            self.report.generation_count += 1
            self.report.save(update_fields=['last_generated', 'last_generated_by', 'generation_count'])
            
            timer.stop()
            
            return {
                'success': True,
                'format': self.report.format,
                'data': result,
                'execution_time_ms': timer.duration_ms()
            }
            
        except Exception as e:
            timer.stop()
            self.report.last_error = str(e)
            self.report.save(update_fields=['last_error'])
            
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': timer.duration_ms()
            }
    
    def _generate_pdf(self, data):
        """Génère un PDF"""
        # À implémenter avec ReportLab ou WeasyPrint
        return {'message': 'PDF generation not implemented'}
    
    def _generate_csv(self, data):
        """Génère un CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        writer.writerow(['Widget', 'Type', 'Data'])
        
        # Données
        for widget in data.get('widgets', []):
            writer.writerow([
                widget['name'],
                widget['type'],
                json.dumps(widget.get('data', {}))
            ])
        
        return output.getvalue()
    
    def _generate_excel(self, data):
        """Génère un Excel"""
        from io import BytesIO
        import pandas as pd
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille des widgets
            widgets_df = pd.DataFrame(data.get('widgets', []))
            widgets_df.to_excel(writer, sheet_name='Widgets', index=False)
            
            # Feuille des KPIs
            kpis_df = pd.DataFrame(data.get('kpis', []))
            kpis_df.to_excel(writer, sheet_name='KPIs', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    def _generate_json(self, data):
        """Génère un JSON"""
        return json.dumps(data, indent=2, default=str)
    
    def _generate_html(self, data):
        """Génère un HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.report.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .widget {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }}
                .kpi {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <h1>{self.report.name}</h1>
            <p>{self.report.description}</p>
            <h2>Widgets</h2>
        """
        
        for widget in data.get('widgets', []):
            html += f"""
            <div class="widget">
                <h3>{widget['name']}</h3>
                <p>Type: {widget['type']}</p>
                <pre>{json.dumps(widget.get('data', {}), indent=2)}</pre>
            </div>
            """
        
        html += """
            <h2>KPIs</h2>
        """
        
        for kpi in data.get('kpis', []):
            html += f"""
            <div class="kpi">
                <h3>{kpi['name']}</h3>
                <p>Valeur: {kpi.get('value', 'N/A')}</p>
                <p>Statut: {kpi.get('status', 'unknown')}</p>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html