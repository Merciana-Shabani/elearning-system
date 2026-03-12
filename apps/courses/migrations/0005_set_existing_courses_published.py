# Data migration: set existing courses to published so they remain visible to students

from django.db import migrations


def set_existing_published(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Course.objects.all().update(status='published')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_instructor_course_status_announcements_prereqs_certificates'),
    ]

    operations = [
        migrations.RunPython(set_existing_published, noop),
    ]
