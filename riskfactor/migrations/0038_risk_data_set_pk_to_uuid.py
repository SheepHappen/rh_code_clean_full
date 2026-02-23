import uuid

from django.db import migrations, models
 
    
class Migration(migrations.Migration):
    dependencies = [
        ('riskfactor', '0037_auto_20200928_0845'),
    ]
    operations = [
        migrations.AlterField(
            model_name='RiskDataSet',
            name='id',
            field=models.CharField(max_length=36, serialize=False, unique=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='RiskDataSet',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]
