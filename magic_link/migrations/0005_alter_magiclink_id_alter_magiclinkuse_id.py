# Generated by Django 4.1.4 on 2023-11-27 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("magic_link", "0004_remove_magiclinkuse_link_is_valid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="magiclink",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="magiclinkuse",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]