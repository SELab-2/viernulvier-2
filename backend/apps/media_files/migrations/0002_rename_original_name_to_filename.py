from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("media_files", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mediafile",
            old_name="original_name",
            new_name="filename",
        ),
    ]
    