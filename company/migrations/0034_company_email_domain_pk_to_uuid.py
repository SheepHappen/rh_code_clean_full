import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('company', '0033_auto_20200923_0812'),
    ]

    operations = [
        migrations.AlterField(
            model_name='CompanyEmailDomain',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
 


