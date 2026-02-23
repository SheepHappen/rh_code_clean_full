import uuid
from django.db import migrations, models


def update_uuids(apps, schema_editor):
    model = apps.get_model("accounts", "UserProfile")
    for record in model.objects.all():
        model.objects.filter(id=record.id).update(id=str(uuid.uuid4()).replace("-", ""))


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0008_auto_20200619_0835'),
    ]

    operations = [
        migrations.AlterField(
            model_name='UserProfile',
            name='id',
            field=models.CharField(max_length=36, serialize=False, unique=False, primary_key=True),
        ),
        migrations.RunPython(update_uuids),
        migrations.AlterField(
            model_name='UserProfile',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
 


