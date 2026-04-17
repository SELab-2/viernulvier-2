from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("genres", "0001_initial"),
        ("productions", "0002_merge_uitdatabank_theme_into_genre"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="genre",
            name="use_as",
        ),
        migrations.DeleteModel(
            name="GenreUseAs",
        ),
    ]
