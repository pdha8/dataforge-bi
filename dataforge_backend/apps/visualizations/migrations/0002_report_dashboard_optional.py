from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('visualizations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='dashboard',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reports',
                to='visualizations.dashboard',
                verbose_name='Tableau de bord source',
            ),
        ),
    ]
