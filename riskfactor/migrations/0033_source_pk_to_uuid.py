import uuid

from django.db import migrations, models
 

class Migration(migrations.Migration):
    dependencies = [
        ('riskfactor', '0032_industry_dataset_pk_to_uuid'),
    ]
    operations = [
        migrations.AlterField(
            model_name='RiskDataSetSource',
            name='id',
            field=models.CharField(max_length=36, serialize=False, unique=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='RiskDataSetSource',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]
