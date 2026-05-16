"""Migration 0003 — Aligne les choix de format Export (supprime png/svg/markdown, ajoute tsv/yaml)"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizations', '0002_report_dashboard_optional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dashboard',
            name='default_export_format',
            field=models.CharField(
                choices=[
                    ('pdf',   '📄 PDF (Document)'),
                    ('excel', '📈 Excel (XLSX)'),
                    ('csv',   '📊 CSV (Tableur)'),
                    ('tsv',   '📑 TSV (Tabulé)'),
                    ('yaml',  '📋 YAML'),
                    ('html',  '🌐 HTML (Web)'),
                    ('json',  '🔧 JSON (API)'),
                ],
                default='pdf',
                max_length=20,
                verbose_name="Format d'export par défaut",
            ),
        ),
        migrations.AlterField(
            model_name='report',
            name='format',
            field=models.CharField(
                choices=[
                    ('pdf',   '📄 PDF (Document)'),
                    ('excel', '📈 Excel (XLSX)'),
                    ('csv',   '📊 CSV (Tableur)'),
                    ('tsv',   '📑 TSV (Tabulé)'),
                    ('yaml',  '📋 YAML'),
                    ('html',  '🌐 HTML (Web)'),
                    ('json',  '🔧 JSON (API)'),
                ],
                default='pdf',
                max_length=20,
                verbose_name='Format',
            ),
        ),
    ]
