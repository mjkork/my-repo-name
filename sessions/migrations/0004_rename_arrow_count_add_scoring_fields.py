from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("practice_sessions", "0003_session_next_focus"),
    ]

    operations = [
        migrations.RenameField(
            model_name="session",
            old_name="arrow_count",
            new_name="total_arrows",
        ),
        migrations.AddField(
            model_name="session",
            name="scoring_arrows",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="session",
            name="target_face",
            field=models.CharField(
                blank=True,
                choices=[
                    ("40cm", "40 cm standard"),
                    ("40cm 3-spot vertical", "40 cm 3-spot vertical"),
                    ("60cm", "60 cm standard"),
                    ("60cm 3-spot", "60 cm 3-spot"),
                    ("80cm", "80 cm"),
                    ("122cm", "122 cm"),
                ],
                max_length=40,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="total_score",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
