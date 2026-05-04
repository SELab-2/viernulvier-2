"""Migration for Tag image and TagTranslation excerpt fields."""
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("tags", "0002_remove_tag_source_type_and_is_external"),
    ]

    operations = [
        migrations.AddField(
            model_name="tag",
            name="image",
            field=models.ImageField(
                upload_to="tag_images/",
                null=True,
                blank=True,
                help_text="Upload an image for this tag.",
                db_comment="Optional image for the tag.",
            ),
        ),
        migrations.AddField(
            model_name="tagtranslation",
            name="excerpt",
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Optional short excerpt or summary of the tag in this language.",
                db_comment="Translated excerpt.",
            ),
        ),
    ]
