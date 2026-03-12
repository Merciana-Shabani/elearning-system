from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_remove_preview_public_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="revision_requests",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="course",
            name="returned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="course",
            name="returned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="courses_returned_for_revision",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("submitted", "Submitted for approval"),
                    ("approved", "Approved"),
                    ("published", "Published"),
                    ("rejected", "Rejected"),
                    ("needs_revision", "Needs revision"),
                ],
                default="draft",
                help_text="Draft → Submit for approval → Moderator approves/rejects → Published",
                max_length=20,
            ),
        ),
    ]

