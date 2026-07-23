import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="anonymoususer",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="created at",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="anonymoususer",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
                verbose_name="updated at",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="authenticateduser",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="created at",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="authenticateduser",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
                verbose_name="updated at",
            ),
            preserve_default=False,
        ),
    ]
