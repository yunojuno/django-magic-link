from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("magic_link", "0006_alter_magiclink_id_alter_magiclinkuse_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="magiclink",
            name="token",
            field=models.CharField(
                default=uuid.uuid4,
                editable=False,
                help_text="Unique login token",
                max_length=36,
                unique=True,
            ),
        ),
    ]
