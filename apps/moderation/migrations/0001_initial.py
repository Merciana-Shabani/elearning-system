from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InstructorRoleApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("motivation", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("decision_reason", models.TextField(blank=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="instructor_role_applications_reviewed", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="instructor_role_applications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "elening_instructor_role_applications", "ordering": ["-submitted_at"]},
        ),
        migrations.CreateModel(
            name="ModerationAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action_type", models.CharField(choices=[("warn", "Warning"), ("suspend", "Suspend"), ("ban", "Ban")], max_length=20)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("moderator", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="moderation_actions_made", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_actions_received", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "elening_moderation_actions", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ModerationDispute",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("status", models.CharField(choices=[("open", "Open"), ("closed", "Closed")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("closure_notes", models.TextField(blank=True)),
                ("against_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="disputes_against", to=settings.AUTH_USER_MODEL)),
                ("closed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="disputes_closed", to=settings.AUTH_USER_MODEL)),
                ("opened_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="disputes_opened", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "elening_moderation_disputes", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField()),
                ("object_id", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("open", "Open"), ("closed", "Closed")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_notes", models.TextField(blank=True)),
                ("content_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype")),
                ("reporter", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_reports_filed", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="content_reports_reviewed", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "elening_content_reports", "ordering": ["-created_at"]},
        ),
    ]

