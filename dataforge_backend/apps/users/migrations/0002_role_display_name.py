from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='display_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nom affiché'),
        ),
    ]
