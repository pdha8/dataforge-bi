# apps/visualizations/services.py
"""
Services pour l'application visualizations
"""
import csv
import json
import re
import yaml
import pandas as pd
from io import BytesIO, StringIO
from typing import Dict, List, Any, Optional, Tuple
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
        Rendu complet du tableau de bord avec fusion des filtres globaux.

        Les filtres globaux du dashboard sont fusionnés avec ceux passés
        par l'utilisateur. Les filtres utilisateur prévalent en cas de conflit
        sur le même champ.
        """
        merged_filters = self._merge_filters(self.dashboard.global_filters or [], filters)

        result = {
            'id': str(self.dashboard.id),
            'name': self.dashboard.name,
            'description': self.dashboard.description,
            'layout': self.dashboard.layout,
            'theme': self.dashboard.theme,
            'global_filters': self.dashboard.global_filters,
            'applied_filters': merged_filters,
            'widgets': [],
            'kpis': []
        }

        # Rendre les widgets
        for widget in self.dashboard.widgets.filter(is_enabled=True):
            try:
                widget_data = self._render_widget(widget, merged_filters)
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
                kpi_data = self._render_kpi(kpi, merged_filters)
                result['kpis'].append(kpi_data)
            except Exception as e:
                result['kpis'].append({
                    'id': str(kpi.id),
                    'name': kpi.name,
                    'error': str(e)
                })

        return result

    @staticmethod
    def _merge_filters(global_filters, user_filters):
        """Fusionne les filtres globaux et utilisateur (user override par field)"""
        if not user_filters:
            return list(global_filters or [])
        if not isinstance(user_filters, list):
            return list(global_filters or [])

        user_fields = {f.get('field') for f in user_filters if isinstance(f, dict) and f.get('field')}
        merged = [f for f in (global_filters or []) if not (isinstance(f, dict) and f.get('field') in user_fields)]
        merged.extend(user_filters)
        return merged
    
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

    # Fonctions d'agrégation autorisées dans les formules KPI
    _SAFE_AGG_FUNCS = {
        'sum':   lambda xs: sum(xs),
        'avg':   lambda xs: (sum(xs) / len(xs)) if xs else 0,
        'mean':  lambda xs: (sum(xs) / len(xs)) if xs else 0,
        'count': lambda xs: len(xs),
        'min':   lambda xs: min(xs) if xs else 0,
        'max':   lambda xs: max(xs) if xs else 0,
        'abs':   abs,
        'round': round,
    }

    def __init__(self, kpi):
        self.kpi = kpi

    def calculate(self, filters=None):
        """
        Calcule la valeur du KPI et met à jour l'historique tendance
        """
        timer = Timer().start()

        try:
            # Conserver l'ancienne valeur AVANT recalcul (sinon previous_value = current_value)
            old_value = self.kpi.current_value

            if self.kpi.formula:
                value = self._calculate_formula(filters)
            elif self.kpi.measure:
                value = self._calculate_measure(filters)
            else:
                value = 0

            trend = None
            trend_percentage = None
            trend_direction = self.kpi.trend_direction or ''

            if old_value is not None and old_value != 0:
                trend_percentage = ((value - old_value) / old_value) * 100
                if trend_percentage > 0:
                    trend = 'up'
                    trend_direction = 'up'
                elif trend_percentage < 0:
                    trend = 'down'
                    trend_direction = 'down'
                else:
                    trend = 'stable'
                    trend_direction = 'stable'

            # Persister - previous_value AVANT current_value
            self.kpi.previous_value = old_value
            self.kpi.current_value = value
            self.kpi.trend_percentage = trend_percentage
            self.kpi.trend_direction = trend_direction
            self.kpi.last_calculated = timezone.now()
            self.kpi.save(update_fields=[
                'current_value', 'previous_value',
                'trend_percentage', 'trend_direction', 'last_calculated'
            ])

            timer.stop()

            return {
                'success': True,
                'value': value,
                'previous_value': old_value,
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
        """
        Évalue la formule KPI de manière sécurisée.

        Supporte deux modes :
        1. Référence à des mesures via mesures du schéma dimensionnel (ex : sum(montant) / count(commandes))
           Les colonnes des résultats sont injectées comme listes nommées.
        2. Expression arithmétique simple (ex : 100 * 0.85)

        Sécurité : utilise compile() avec __builtins__ vide pour bloquer
        import, open, exec, eval, etc.
        """
        formula = (self.kpi.formula or '').strip()
        if not formula:
            return 0

        # Construire le contexte (colonnes du schéma dimensionnel)
        context = {}
        if self.kpi.dimensional_schema:
            service = DimensionalSchemaService(self.kpi.dimensional_schema)
            result = service.execute(filters)
            if result.get('success') and result.get('data'):
                rows = result['data']
                if rows and isinstance(rows[0], dict):
                    for col in rows[0].keys():
                        context[col] = [row.get(col, 0) for row in rows]

        # Construire les fonctions autorisées
        safe_globals = {'__builtins__': {}}
        safe_locals = {**self._SAFE_AGG_FUNCS, **context}

        try:
            # compile() avec mode 'eval' refuse statements (import, def, etc.)
            code = compile(formula, '<kpi-formula>', 'eval')

            # Vérification supplémentaire : noms réservés interdits
            forbidden = {'__import__', 'eval', 'exec', 'compile', 'open', 'globals', 'locals'}
            for name in code.co_names:
                if name in forbidden:
                    raise ValueError(f"Nom interdit dans la formule: {name}")

            result = eval(code, safe_globals, safe_locals)
            return float(result) if result is not None else 0
        except (SyntaxError, NameError, TypeError, ZeroDivisionError, ValueError):
            return 0

    def _calculate_measure(self, filters=None):
        """Calcul via mesure"""
        if not self.kpi.dimensional_schema or not self.kpi.measure:
            return 0

        service = DimensionalSchemaService(self.kpi.dimensional_schema)
        result = service.execute(filters)

        if result['success'] and result['data']:
            agg_func = (self.kpi.aggregation or 'sum').upper()
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

    # (content, content_type, file_extension)
    _FORMAT_MAP = {
        'csv':   ('text/csv; charset=utf-8',                                                          'csv'),
        'tsv':   ('text/tab-separated-values; charset=utf-8',                                         'tsv'),
        'json':  ('application/json; charset=utf-8',                                                  'json'),
        'yaml':  ('application/x-yaml; charset=utf-8',                                               'yaml'),
        'html':  ('text/html; charset=utf-8',                                                         'html'),
        'xlsx':  ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',                'xlsx'),
        'pdf':   ('application/pdf',                                                                  'pdf'),
    }

    def __init__(self, report):
        self.report = report

    def generate(self, user=None) -> dict:
        timer = Timer().start()
        try:
            # Dashboard peut être None (champ optionnel)
            if self.report.dashboard:
                data = DashboardService(self.report.dashboard).render(self.report.filters)
            else:
                data = {
                    'id': str(self.report.id),
                    'name': self.report.name,
                    'description': self.report.description,
                    'widgets': [],
                    'kpis': [],
                }

            fmt = self.report.format
            generators = {
                'pdf':   self._generate_pdf,
                'csv':   self._generate_csv,
                'tsv':   self._generate_tsv,
                'xlsx':  self._generate_excel,
                'json':  self._generate_json,
                'yaml':  self._generate_yaml,
                'html':  self._generate_html,
            }
            generator = generators.get(fmt, self._generate_json)
            raw_content = generator(data)

            content_type, ext = self._FORMAT_MAP.get(fmt, ('application/octet-stream', 'bin'))
            content: bytes = raw_content if isinstance(raw_content, bytes) else raw_content.encode('utf-8')

            safe_name = re.sub(r'[^\w\-]', '_', self.report.name)[:60]
            filename = f"{safe_name}.{ext}"

            self.report.last_generated = timezone.now()
            self.report.last_generated_by = user
            self.report.generation_count += 1
            self.report.last_error = ''
            self.report.save(update_fields=['last_generated', 'last_generated_by', 'generation_count', 'last_error'])

            timer.stop()
            return {
                'success': True,
                'content': content,
                'content_type': content_type,
                'filename': filename,
                'execution_time_ms': timer.duration_ms(),
            }

        except Exception as e:
            timer.stop()
            self.report.last_error = str(e)
            self.report.save(update_fields=['last_error'])
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': timer.duration_ms(),
            }

    # ── Générateurs ──────────────────────────────────────────────────────────

    # ── PDF helpers ───────────────────────────────────────────

    @staticmethod
    def _rows_to_html_table(rows: list, max_rows: int = 40) -> str:
        """Convert list-of-dicts to a styled HTML table."""
        if not rows:
            return ''
        cols = list(dict.fromkeys(k for row in rows[:max_rows] for k in row.keys()))
        header = ''.join(f'<th>{c}</th>' for c in cols)
        body_rows = []
        for i, row in enumerate(rows[:max_rows]):
            cls = 'tr-alt' if i % 2 else ''
            cells = ''.join(f'<td>{row.get(c, "")}</td>' for c in cols)
            body_rows.append(f'<tr class="{cls}">{cells}</tr>')
        extra = ''
        if len(rows) > max_rows:
            extra = f'<tr><td colspan="{len(cols)}" class="td-more">… {len(rows)-max_rows} lignes supplémentaires non affichées</td></tr>'
        return (
            f'<table class="data-table">'
            f'<thead><tr>{header}</tr></thead>'
            f'<tbody>{"".join(body_rows)}{extra}</tbody>'
            f'</table>'
        )

    @staticmethod
    def _render_widget_body(widget: dict) -> str:
        """Turn widget rendered data into readable HTML (no raw JSON)."""
        rendered = widget.get('data') or {}
        dtype = rendered.get('type', '') if isinstance(rendered, dict) else ''

        if dtype == 'metric':
            val  = rendered.get('value', 'N/A')
            unit = rendered.get('unit', '')
            fmt  = rendered.get('format', '')
            return (
                f'<div class="metric-box">'
                f'<span class="metric-val">{val}</span>'
                f'<span class="metric-unit">{unit}</span>'
                f'</div>'
            )

        if dtype == 'text':
            return f'<p class="widget-text">{rendered.get("content","")}</p>'

        # chart / table / default — extract inner data list
        inner = rendered.get('data') if isinstance(rendered, dict) else rendered
        if isinstance(inner, list) and inner and isinstance(inner[0], dict):
            table = ReportGenerationService._rows_to_html_table(inner)
            return table or '<p class="no-data">Aucune ligne de données</p>'

        if isinstance(inner, list) and inner:
            items = ''.join(f'<li>{item}</li>' for item in inner[:30])
            return f'<ul class="simple-list">{items}</ul>'

        # Fallback : key-value scalar pairs from the rendered dict
        if isinstance(rendered, dict):
            pairs = {k: v for k, v in rendered.items()
                     if k not in ('type', 'chart_type', 'config', 'style')
                     and not isinstance(v, (dict, list))}
            if pairs:
                rows_html = ''.join(
                    f'<tr><td class="kv-key">{k}</td><td>{v}</td></tr>'
                    for k, v in pairs.items()
                )
                return f'<table class="kv-table"><tbody>{rows_html}</tbody></table>'

        return '<p class="no-data">Aucune donnée disponible pour ce widget.</p>'

    def _generate_pdf(self, data) -> bytes:
        try:
            import weasyprint
        except (ImportError, OSError) as exc:
            raise RuntimeError(
                "WeasyPrint ne peut pas charger les bibliothèques système requises (libpango, libcairo). "
                "Exécutez sur le serveur : "
                "sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0"
            ) from exc

        page_size   = (getattr(self.report, 'page_size',   None) or 'A4').upper()
        orientation = (getattr(self.report, 'orientation', None) or 'portrait').lower()
        css_page    = f'size: {page_size} {orientation}; margin: 1.8cm 2.2cm 2cm 2.2cm;'

        generated_at  = timezone.now().strftime('%d/%m/%Y à %H:%M')
        dashboard_name = data.get('name', self.report.name)
        widgets = data.get('widgets', [])
        kpis    = data.get('kpis', [])

        # ── KPI cards ─────────────────────────────────────────
        STATUS_COLORS = {'critical': '#dc2626', 'warning': '#d97706', 'good': '#16a34a', 'excellent': '#0284c7'}

        def kpi_card(k):
            color  = STATUS_COLORS.get(k.get('status', ''), '#374151')
            trend  = k.get('trend', '')
            trend_icon = {'up': '▲', 'down': '▼', 'stable': '→'}.get(trend, '')
            trend_pct  = k.get('trend_percentage')
            trend_str  = f'{trend_icon} {trend_pct:.1f}%' if trend_pct is not None else trend_icon
            target_str = f'Objectif : {k.get("target","")} {k.get("unit","")}'.strip() if k.get('target') else ''
            return (
                f'<div class="kpi-card">'
                f'<div class="kpi-name">{k.get("name","")}</div>'
                f'<div class="kpi-value" style="color:{color}">{k.get("value","N/A")} <span class="kpi-unit">{k.get("unit","")}</span></div>'
                f'<div class="kpi-trend">{trend_str}</div>'
                f'<div class="kpi-target">{target_str}</div>'
                f'</div>'
            )

        kpis_html = ''.join(kpi_card(k) for k in kpis) if kpis else '<p class="empty-msg">Aucun KPI dans ce rapport.</p>'

        # ── Widget sections ────────────────────────────────────
        def widget_section(w):
            body = ReportGenerationService._render_widget_body(w)
            badge_map = {
                'chart': ('Graphique', '#2563eb'),
                'table': ('Tableau',   '#059669'),
                'metric':('Métrique',  '#7c3aed'),
                'text':  ('Texte',     '#6b7280'),
            }
            wtype  = w.get('type', '')
            blabel, bcolor = badge_map.get(wtype, (wtype.capitalize(), '#6b7280'))
            return (
                f'<div class="widget-block">'
                f'<div class="widget-header">'
                f'<span class="widget-title">{w.get("name","Sans nom")}</span>'
                f'<span class="widget-badge" style="background:{bcolor}20;color:{bcolor}">{blabel}</span>'
                f'</div>'
                f'<div class="widget-body">{body}</div>'
                f'</div>'
            )

        widgets_html = ''.join(widget_section(w) for w in widgets) if widgets else '<p class="empty-msg">Aucun widget dans ce rapport.</p>'

        # ── Métadonnées rapport ────────────────────────────────
        meta_rows = []
        if self.report.schedule:
            meta_rows.append(('Planification', self.report.schedule))
        if self.report.owner:
            meta_rows.append(('Propriétaire', str(self.report.owner)))
        if self.report.generation_count:
            meta_rows.append(('Nombre de générations', str(self.report.generation_count)))
        meta_html = ''.join(
            f'<tr><td class="meta-key">{k}</td><td>{v}</td></tr>' for k, v in meta_rows
        )

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{self.report.name}</title>
<style>
  @page {{
    {css_page}
    @top-left   {{ content: "{self.report.name}"; font-size: 7.5pt; color: #9ca3af; font-family: sans-serif; }}
    @top-right  {{ content: "Page " counter(page) " / " counter(pages); font-size: 7.5pt; color: #9ca3af; font-family: sans-serif; }}
    @bottom-right {{ content: "SOTIFibre BI · {generated_at}"; font-size: 7pt; color: #d1d5db; font-family: sans-serif; }}
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: DejaVu Sans, Arial, Helvetica, sans-serif;
    font-size: 9.5pt;
    color: #111827;
    line-height: 1.55;
    background: #fff;
  }}

  /* ── Cover header ── */
  .report-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    border-bottom: 3px solid #1d4ed8;
    padding-bottom: 14pt;
    margin-bottom: 20pt;
  }}
  .brand {{
    font-size: 11pt;
    font-weight: 700;
    color: #1d4ed8;
    letter-spacing: 0.5px;
  }}
  .brand-sub {{ font-size: 7.5pt; color: #6b7280; font-weight: 400; }}
  .report-title {{ font-size: 19pt; font-weight: 700; color: #111827; line-height: 1.2; margin-bottom: 4pt; }}
  .report-desc  {{ font-size: 9pt; color: #6b7280; margin-bottom: 6pt; }}
  .report-meta-badge {{
    display: inline-block;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4pt;
    padding: 2pt 8pt;
    font-size: 8pt;
    color: #1d4ed8;
    margin-right: 6pt;
  }}

  /* ── Section headings ── */
  h2 {{
    font-size: 12pt;
    font-weight: 700;
    color: #1d4ed8;
    margin: 20pt 0 10pt 0;
    padding-bottom: 4pt;
    border-bottom: 1.5px solid #dbeafe;
  }}
  h3 {{ font-size: 10pt; color: #374151; margin-bottom: 6pt; }}

  /* ── KPI cards ── */
  .kpi-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 10pt;
    margin-bottom: 4pt;
  }}
  .kpi-card {{
    flex: 1 1 130pt;
    border: 1px solid #e5e7eb;
    border-radius: 6pt;
    padding: 10pt 12pt;
    page-break-inside: avoid;
    background: #fafafa;
  }}
  .kpi-name  {{ font-size: 7.5pt; color: #6b7280; margin-bottom: 4pt; text-transform: uppercase; letter-spacing: 0.4px; }}
  .kpi-value {{ font-size: 20pt; font-weight: 700; line-height: 1.1; }}
  .kpi-unit  {{ font-size: 10pt; font-weight: 400; color: #9ca3af; }}
  .kpi-trend {{ font-size: 8pt; color: #6b7280; margin-top: 4pt; }}
  .kpi-target{{ font-size: 7.5pt; color: #9ca3af; margin-top: 2pt; }}

  /* ── Widget blocks ── */
  .widget-block {{
    border: 1px solid #e5e7eb;
    border-radius: 6pt;
    margin-bottom: 14pt;
    page-break-inside: avoid;
    overflow: hidden;
  }}
  .widget-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    padding: 7pt 10pt;
  }}
  .widget-title {{ font-size: 10pt; font-weight: 600; color: #111827; }}
  .widget-badge {{
    font-size: 7pt;
    font-weight: 600;
    padding: 2pt 7pt;
    border-radius: 99pt;
    letter-spacing: 0.3px;
  }}
  .widget-body {{ padding: 10pt; }}

  /* ── Data tables ── */
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
    margin-top: 4pt;
  }}
  .data-table thead tr {{ background: #1d4ed8; color: #fff; }}
  .data-table th {{
    padding: 5pt 7pt;
    text-align: left;
    font-weight: 600;
    font-size: 7.5pt;
    letter-spacing: 0.2px;
  }}
  .data-table td {{ padding: 4pt 7pt; border-bottom: 1px solid #f3f4f6; color: #374151; }}
  .data-table .tr-alt td {{ background: #f9fafb; }}
  .data-table .td-more {{ text-align: center; color: #9ca3af; font-style: italic; background: #f9fafb; }}

  /* ── KV table (key-value) ── */
  .kv-table {{ width: 100%; border-collapse: collapse; font-size: 8pt; }}
  .kv-table td {{ padding: 4pt 8pt; border-bottom: 1px solid #f3f4f6; }}
  .kv-key {{ font-weight: 600; color: #374151; width: 35%; background: #f9fafb; }}

  /* ── Metric display ── */
  .metric-box {{ text-align: center; padding: 12pt; }}
  .metric-val  {{ font-size: 28pt; font-weight: 700; color: #1d4ed8; }}
  .metric-unit {{ font-size: 12pt; color: #9ca3af; }}

  /* ── Report metadata table ── */
  .meta-table {{ font-size: 8pt; width: 100%; border-collapse: collapse; margin-top: 8pt; }}
  .meta-table td {{ padding: 3pt 8pt; border-bottom: 1px solid #f3f4f6; }}
  .meta-key {{ font-weight: 600; color: #6b7280; width: 35%; }}

  /* ── Misc ── */
  .empty-msg  {{ color: #9ca3af; font-style: italic; font-size: 9pt; padding: 8pt 0; }}
  .no-data    {{ color: #9ca3af; font-size: 8pt; padding: 6pt 0; }}
  .widget-text {{ font-size: 9pt; color: #374151; line-height: 1.6; }}
  .simple-list {{ padding-left: 16pt; font-size: 8pt; color: #374151; }}
  .simple-list li {{ margin-bottom: 2pt; }}
</style>
</head>
<body>

<!-- ── En-tête du rapport ───────────────────────── -->
<div class="report-header">
  <div>
    <div class="report-title">{self.report.name}</div>
    {f'<div class="report-desc">{self.report.description}</div>' if self.report.description else ''}
    <div style="margin-top:6pt">
      <span class="report-meta-badge">Format : PDF</span>
      <span class="report-meta-badge">Dashboard : {dashboard_name}</span>
      <span class="report-meta-badge">Généré le {generated_at}</span>
    </div>
  </div>
  <div style="text-align:right">
    <div class="brand">SOTIFibre BI</div>
    <div class="brand-sub">Plateforme d'Intelligence Économique</div>
  </div>
</div>

{f'''<!-- ── Métadonnées ─────────────────────────────── -->
<table class="meta-table"><tbody>{meta_html}</tbody></table>''' if meta_html else ''}

<!-- ── KPIs ─────────────────────────────────────── -->
<h2>Indicateurs clés ({len(kpis)})</h2>
<div class="kpi-grid">
{kpis_html}
</div>

<!-- ── Widgets ───────────────────────────────────── -->
<h2>Widgets ({len(widgets)})</h2>
{widgets_html}

</body>
</html>"""

        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        return pdf_bytes

    def _generate_csv(self, data) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Widget', 'Type', 'Données'])
        for widget in data.get('widgets', []):
            writer.writerow([widget.get('name', ''), widget.get('type', ''), json.dumps(widget.get('data', {}), ensure_ascii=False)])
        writer.writerow([])
        writer.writerow(['KPI', 'Valeur', 'Statut'])
        for kpi in data.get('kpis', []):
            writer.writerow([kpi.get('name', ''), kpi.get('value', ''), kpi.get('status', '')])
        return output.getvalue()

    def _generate_tsv(self, data) -> str:
        output = StringIO()
        writer = csv.writer(output, delimiter='\t')
        writer.writerow(['Widget', 'Type', 'Données'])
        for widget in data.get('widgets', []):
            writer.writerow([widget.get('name', ''), widget.get('type', ''), json.dumps(widget.get('data', {}), ensure_ascii=False)])
        writer.writerow([])
        writer.writerow(['KPI', 'Valeur', 'Statut'])
        for kpi in data.get('kpis', []):
            writer.writerow([kpi.get('name', ''), kpi.get('value', ''), kpi.get('status', '')])
        return output.getvalue()

    def _generate_excel(self, data) -> bytes:
        output = BytesIO()
        widgets_rows = [
            {'Widget': w.get('name', ''), 'Type': w.get('type', ''), 'Données': json.dumps(w.get('data', {}), ensure_ascii=False)}
            for w in data.get('widgets', [])
        ]
        kpis_rows = [
            {'KPI': k.get('name', ''), 'Valeur': k.get('value', ''), 'Statut': k.get('status', '')}
            for k in data.get('kpis', [])
        ]
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(widgets_rows or [{}]).to_excel(writer, sheet_name='Widgets', index=False)
            pd.DataFrame(kpis_rows or [{}]).to_excel(writer, sheet_name='KPIs', index=False)
        output.seek(0)
        return output.read()

    def _generate_json(self, data) -> str:
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)

    def _generate_yaml(self, data) -> str:
        sanitized = json.loads(json.dumps(data, default=str))
        return yaml.dump(sanitized, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def _generate_html(self, data) -> str:
        widgets_html = ''.join(
            f'<div class="widget"><h3>{w.get("name","")}</h3>'
            f'<p>Type : {w.get("type","")}</p>'
            f'<pre>{json.dumps(w.get("data",{}), indent=2, ensure_ascii=False)}</pre></div>'
            for w in data.get('widgets', [])
        )
        kpis_html = ''.join(
            f'<div class="kpi"><strong>{k.get("name","")}</strong>'
            f'<span>{k.get("value","N/A")}</span></div>'
            for k in data.get('kpis', [])
        )
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{self.report.name}</title>
  <style>
    body{{font-family:Arial,sans-serif;margin:24px;color:#1a1a1a}}
    h1{{border-bottom:2px solid #333;padding-bottom:8px}}
    .widget{{margin:16px 0;padding:12px;border:1px solid #ddd;border-radius:4px}}
    .kpi{{display:inline-block;margin:8px;padding:12px 20px;background:#f0f4ff;border-radius:6px}}
    pre{{background:#f5f5f5;padding:8px;overflow:auto;font-size:12px}}
  </style>
</head>
<body>
  <h1>{self.report.name}</h1>
  <p>{self.report.description}</p>
  <h2>Widgets ({len(data.get('widgets',[]))})</h2>
  {widgets_html or '<p><em>Aucun widget</em></p>'}
  <h2>KPIs ({len(data.get('kpis',[]))})</h2>
  <div>{kpis_html or '<p><em>Aucun KPI</em></p>'}</div>
</body>
</html>"""