"""
Migration 0004 — Standardisation : format 'excel' → 'xlsx' partout
"""
from django.db import migrations, models


def excel_to_xlsx(apps, schema_editor):
    Report = apps.get_model('visualizations', 'Report')
    Report.objects.filter(format='excel').update(format='xlsx')
    Dashboard = apps.get_model('visualizations', 'Dashboard')
    Dashboard.objects.filter(default_export_format='excel').update(default_export_format='xlsx')


def xlsx_to_excel(apps, schema_editor):
    Report = apps.get_model('visualizations', 'Report')
    Report.objects.filter(format='xlsx').update(format='excel')
    Dashboard = apps.get_model('visualizations', 'Dashboard')
    Dashboard.objects.filter(default_export_format='xlsx').update(default_export_format='excel')


XLSX_CHOICES = [
    ('pdf',  '📄 PDF (Document)'),
    ('xlsx', '📈 Excel (XLSX)'),
    ('csv',  '📊 CSV (Tableur)'),
    ('tsv',  '📑 TSV (Tabulé)'),
    ('yaml', '📋 YAML'),
    ('html', '🌐 HTML (Web)'),
    ('json', '🔧 JSON (API)'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('visualizations', '0003_report_format_choices'),
    ]

    operations = [
        migrations.RunPython(excel_to_xlsx, xlsx_to_excel),
        migrations.AlterField(
            model_name='report',
            name='format',
            field=models.CharField(
                choices=XLSX_CHOICES,
                default='pdf',
                max_length=20,
                verbose_name='Format',
            ),
        ),
        migrations.AlterField(
            model_name='dashboard',
            name='default_export_format',
            field=models.CharField(
                choices=XLSX_CHOICES,
                default='pdf',
                max_length=20,
                verbose_name="Format d'export par défaut",
            ),
        ),
    ]
