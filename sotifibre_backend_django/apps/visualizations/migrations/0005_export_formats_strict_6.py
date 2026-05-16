"""
Migration 0005 — Standardisation des formats d'export aux 6 formats officiels :
  xlsx, csv, yaml, json, tsv, html

Suppression du format 'pdf' au profit de 'html' (les rapports HTML peuvent
être convertis côté serveur en PDF via WeasyPrint, mais le format choisi
par l'utilisateur reste HTML).
"""
from django.db import migrations, models


SIX_FORMATS = [
    ('xlsx', '📈 Excel (XLSX)'),
    ('csv',  '📊 CSV (Tableur)'),
    ('yaml', '📋 YAML'),
    ('json', '🔧 JSON (API)'),
    ('tsv',  '📑 TSV (Tabulé)'),
    ('html', '🌐 HTML (Web)'),
]


def pdf_to_html(apps, schema_editor):
    """Tous les rapports/dashboards qui étaient en `pdf` passent en `html`."""
    Report    = apps.get_model('visualizations', 'Report')
    Dashboard = apps.get_model('visualizations', 'Dashboard')
    Report.objects.filter(format='pdf').update(format='html')
    Dashboard.objects.filter(default_export_format='pdf').update(default_export_format='html')


def html_to_pdf(apps, schema_editor):
    """Rollback : non-réversible métier, on garde 'html' (aucune perte)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('visualizations', '0004_report_format_excel_to_xlsx'),
    ]

    operations = [
        migrations.RunPython(pdf_to_html, html_to_pdf),
        migrations.AlterField(
            model_name='report',
            name='format',
            field=models.CharField(
                choices=SIX_FORMATS,
                default='html',
                max_length=20,
                verbose_name='Format',
            ),
        ),
        migrations.AlterField(
            model_name='dashboard',
            name='default_export_format',
            field=models.CharField(
                choices=SIX_FORMATS,
                default='html',
                max_length=20,
                verbose_name="Format d'export par défaut",
            ),
        ),
    ]
