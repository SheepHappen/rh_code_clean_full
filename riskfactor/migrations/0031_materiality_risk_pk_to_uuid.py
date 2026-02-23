import uuid

from django.db import migrations, models
 

class Migration(migrations.Migration):
    dependencies = [
        ('riskfactor', '0030_country_risk_pk_to_uuid'),
    ]
    operations = [
        migrations.AlterField(
            model_name='MaterialityRisk',
            name='id',
            field=models.CharField(max_length=36, serialize=False, unique=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='MaterialityRisk',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]

