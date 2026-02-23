import uuid

from django.db import migrations, models
 

class Migration(migrations.Migration):
    dependencies = [
         ('company', '0039_reccomendtations_pk_to_uuid'),
    ]
    operations = [
        migrations.AlterField(
            model_name='ManagementQuestionAnswerSet',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]

