import uuid

from django.db import migrations, models

    
class Migration(migrations.Migration):
    dependencies = [
         ('company', '0036_auto_20200924_1416'),
    ]
    operations = [
        migrations.AlterField(
            model_name='CompanyFund',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]

