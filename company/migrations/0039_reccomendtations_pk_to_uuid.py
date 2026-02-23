import uuid

from django.db import migrations, models
 
    
class Migration(migrations.Migration):
    dependencies = [
         ('company', '0038_industry_pk_to_uuid'),
    ]
    operations = [
        migrations.AlterField(
            model_name='AssessmentIssueRecommendations',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True),
        ),
    ]

