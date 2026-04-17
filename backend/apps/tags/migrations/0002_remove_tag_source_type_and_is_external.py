from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tag",
            name="source_type",
        ),
        migrations.RemoveField(
            model_name="tag",
            name="is_external",
        ),
    ]
