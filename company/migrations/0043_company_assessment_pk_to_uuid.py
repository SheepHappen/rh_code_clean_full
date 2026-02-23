import uuid

from django.db import migrations, models
 

class Migration(migrations.Migration):
    dependencies = [
        ('company', '0042_auto_20200925_1304'),
    ]
    operations = [
        migrations.AlterField(
            model_name='CompanyAssessment',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]

