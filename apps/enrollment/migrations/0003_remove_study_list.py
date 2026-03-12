# Remove StudyList model (study list feature removed)
# Drops elening_study_list table if it exists (from previous 0003_study_list migration).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS elening_study_list;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
