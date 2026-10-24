import apps.authentication.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_user_otp_purpose_user_token_version_alter_user_otp"),
    ]

    operations = [
        migrations.AddField(
            model_name="guestuser",
            name="expires_at",
            field=models.DateTimeField(
                db_index=True,
                default=apps.authentication.models.guest_user_expiration,
                verbose_name="expires at",
            ),
        ),
    ]
