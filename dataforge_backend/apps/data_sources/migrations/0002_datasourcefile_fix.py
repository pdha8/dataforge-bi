"""
Migration 0002 — DataSourceFile : FK nullable, champ file_type, champ name
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_sources', '0001_initial'),
    ]

    operations = [
        # data_source devient nullable (les fichiers peuvent exister sans source)
        migrations.AlterField(
            model_name='datasourcefile',
            name='data_source',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='files',
                to='data_sources.datasource',
                verbose_name='Source de données',
            ),
        ),
        # Nom affiché (display name) séparé du nom original du fichier
        migrations.AddField(
            model_name='datasourcefile',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Nom affiché'),
        ),
        # Type de fichier sélectionnable (csv, xlsx, yaml, json, tsv, html)
        migrations.AddField(
            model_name='datasourcefile',
            name='file_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('csv',  '📊 CSV'),
                    ('xlsx', '📈 Excel (XLSX)'),
                    ('yaml', '📋 YAML'),
                    ('json', '🔧 JSON'),
                    ('tsv',  '📑 TSV (Tabulé)'),
                    ('html', '🌐 HTML'),
                ],
                default='csv',
                max_length=20,
                verbose_name='Type de fichier',
            ),
        ),
    ]
