from django.db import migrations


def _forwards_merge_theme_into_genres(apps, _schema_editor):
    Production = apps.get_model("productions", "Production")
    ProductionGenre = apps.get_model("productions", "ProductionGenre")
    UitDatabaseTheme = apps.get_model("productions", "UitDatabaseTheme")

    Genre = apps.get_model("genres", "Genre")
    GenreUseAs = apps.get_model("genres", "GenreUseAs")
    GenreTranslation = apps.get_model("genres", "GenreTranslation")
    Language = apps.get_model("languages", "Language")

    use_as_obj, _ = GenreUseAs.objects.get_or_create(name="genre")
    language = Language.objects.filter(code="nl").first() or Language.objects.filter(code="en").first() or Language.objects.first()

    theme_to_genre: dict[int, int] = {}

    for theme in UitDatabaseTheme.objects.all().iterator():
        external_id = theme.external_id or f"/legacy/uitdatabank/themes/{theme.pk}"
        genre, created = Genre.objects.get_or_create(
            external_id=external_id,
            defaults={
                "type": "uitdatabank_theme",
                "use_as_id": use_as_obj.pk,
                "vendor_id": theme.name,
            },
        )

        if not created and not genre.vendor_id and theme.name:
            genre.vendor_id = theme.name
            genre.save(update_fields=["vendor_id"])

        if language and theme.name:
            GenreTranslation.objects.get_or_create(
                genre_id=genre.pk,
                language_id=language.pk,
                defaults={"name": theme.name[:50]},
            )

        theme_to_genre[theme.pk] = genre.pk

    if not theme_to_genre:
        return

    for production in Production.objects.exclude(uit_database_theme_id__isnull=True).only("id", "uit_database_theme_id").iterator():
        genre_id = theme_to_genre.get(production.uit_database_theme_id)
        if genre_id is None:
            continue

        if ProductionGenre.objects.filter(production_id=production.pk, genre_id=genre_id).exists():
            continue

        current_max = (
            ProductionGenre.objects.filter(production_id=production.pk)
            .order_by("-position")
            .values_list("position", flat=True)
            .first()
        )

        ProductionGenre.objects.create(
            production_id=production.pk,
            genre_id=genre_id,
            position=(current_max or 0) + 1,
        )


def _backwards_noop(_apps, _schema_editor):
    # Backwards is intentionally a no-op.
    # Recreating a removed theme model and restoring one exact FK choice
    # from many production genres is lossy and not deterministic.
    return


class Migration(migrations.Migration):

    dependencies = [
        ("genres", "0001_initial"),
        ("languages", "0001_initial"),
        ("productions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_forwards_merge_theme_into_genres, _backwards_noop),
        migrations.RemoveField(
            model_name="production",
            name="uit_database_theme",
        ),
        migrations.DeleteModel(
            name="UitDatabaseTheme",
        ),
    ]
