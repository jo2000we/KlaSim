from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('config', '0002_add_promptconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfig',
            name='simulation_password_hash',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
