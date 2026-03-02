from django import forms

from apps.core.bulk import (
    BaseBulkAction,
    BulkResult,
    DynamicBulkService,
    choice_field_spec,
    datetime_field_spec,
    fk_field_spec,
    m2m_field_spec,
    text_field_spec,
)
from apps.events.models import Event
from apps.locations.models import Hall
from apps.productions.models import Production, UitDatabaseTheme, UitDatabaseType
from apps.genres.models import Genre
from apps.tags.models import Tag


class AddTagAction(BaseBulkAction):
    slug = "add_tag"
    label = "Add tag"
    form_fields = {
        "tag": forms.ModelChoiceField(queryset=Tag.objects.all(), label="Tag", required=True),
    }

    def run(self, qs, cleaned, user):
        tag = cleaned["tag"]
        through = Production.tags.through
        ids = list(qs.values_list("id", flat=True))
        rows = [through(production_id=pid, tag_id=tag.id) for pid in ids]
        created = through.objects.bulk_create(rows, ignore_conflicts=True, batch_size=1000)
        return BulkResult(matched=len(ids), processed=len(created), detail="Tags added")


class RemoveTagAction(BaseBulkAction):
    slug = "remove_tag"
    label = "Remove tag"
    form_fields = {
        "tag": forms.ModelChoiceField(queryset=Tag.objects.all(), label="Tag", required=True),
    }

    def run(self, qs, cleaned, user):
        tag = cleaned["tag"]
        deleted, _ = Production.tags.through.objects.filter(
            production_id__in=qs.values_list("id", flat=True),
            tag=tag,
        ).delete()
        return BulkResult(matched=qs.count(), processed=deleted, detail="Tags removed")


class UpdateHallEventsAction(BaseBulkAction):
    slug = "set_hall_on_events"
    label = "Set hall on events"
    form_fields = {
        "hall": forms.ModelChoiceField(queryset=Hall.objects.all(), label="Hall", required=True),
    }

    def run(self, qs, cleaned, user):
        hall = cleaned["hall"]
        updated = Event.objects.filter(production__in=qs).update(hall=hall)
        return BulkResult(matched=qs.count(), processed=updated, detail="Events updated")


class DeleteEventsAction(BaseBulkAction):
    slug = "delete_events"
    label = "Delete events"
    form_fields = {}

    def run(self, qs, cleaned, user):
        deleted, _ = Event.objects.filter(production__in=qs).delete()
        return BulkResult(matched=qs.count(), processed=deleted, detail="Events deleted")


class ClearTagsAction(BaseBulkAction):
    slug = "clear_tags"
    label = "Clear all tags"
    form_fields = {}

    def run(self, qs, cleaned, user):
        deleted, _ = Production.tags.through.objects.filter(
            production_id__in=qs.values_list("id", flat=True)
        ).delete()
        return BulkResult(matched=qs.count(), processed=deleted, detail="All tags cleared")


class ReplaceTagsAction(BaseBulkAction):
    slug = "replace_tags"
    label = "Replace tags"
    form_fields = {
        "tags": forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), label="Tags", required=False),
    }

    def run(self, qs, cleaned, user):
        tag_ids = list(cleaned.get("tags", []))
        ids = list(qs.values_list("id", flat=True))
        through = Production.tags.through
        through.objects.filter(production_id__in=ids).delete()
        rows = [through(production_id=pid, tag_id=tid) for pid in ids for tid in tag_ids]
        created = through.objects.bulk_create(rows, ignore_conflicts=True, batch_size=1000)
        return BulkResult(matched=len(ids), processed=len(created), detail="Tags replaced")


class SetAttendanceModeAction(BaseBulkAction):
    slug = "set_attendance_mode"
    label = "Set attendance mode"
    form_fields = {
        "attendance_mode": forms.ChoiceField(
            choices=Production.AttendanceMode.choices, label="Attendance mode", required=True
        )
    }

    def run(self, qs, cleaned, user):
        mode = cleaned["attendance_mode"]
        updated = qs.update(attendance_mode=mode)
        return BulkResult(matched=qs.count(), processed=updated, detail="Attendance mode updated")


class SetPerformerTypeAction(BaseBulkAction):
    slug = "set_performer_type"
    label = "Set performer type"
    form_fields = {
        "performer_type": forms.ChoiceField(
            choices=Production.PerformerType.choices, label="Performer type", required=True
        )
    }

    def run(self, qs, cleaned, user):
        performer_type = cleaned["performer_type"]
        updated = qs.update(performer_type=performer_type)
        return BulkResult(matched=qs.count(), processed=updated, detail="Performer type updated")


class SetUitThemeAction(BaseBulkAction):
    slug = "set_uit_theme"
    label = "Set UIT theme"
    form_fields = {
        "uit_theme": forms.ModelChoiceField(queryset=UitDatabaseTheme.objects.all(), label="UIT theme", required=False)
    }

    def run(self, qs, cleaned, user):
        updated = qs.update(uit_database_theme=cleaned.get("uit_theme"))
        return BulkResult(matched=qs.count(), processed=updated, detail="UIT theme updated")


class SetUitTypeAction(BaseBulkAction):
    slug = "set_uit_type"
    label = "Set UIT type"
    form_fields = {
        "uit_type": forms.ModelChoiceField(queryset=UitDatabaseType.objects.all(), label="UIT type", required=False)
    }

    def run(self, qs, cleaned, user):
        updated = qs.update(uit_database_type=cleaned.get("uit_type"))
        return BulkResult(matched=qs.count(), processed=updated, detail="UIT type updated")


class ClearHallEventsAction(BaseBulkAction):
    slug = "clear_hall_events"
    label = "Clear hall on events"
    form_fields = {}

    def run(self, qs, cleaned, user):
        updated = Event.objects.filter(production__in=qs).update(hall=None)
        return BulkResult(matched=qs.count(), processed=updated, detail="Event halls cleared")


class ProductionBulkService(DynamicBulkService):
    model = Production
    
    field_specs = (
        choice_field_spec("performer_type", "Performer type", Production.PerformerType.choices),
        choice_field_spec("attendance_mode", "Attendance mode", Production.AttendanceMode.choices),
        fk_field_spec("uit_database_theme", "UIT theme", queryset=UitDatabaseTheme.objects.all()),
        fk_field_spec("uit_database_type", "UIT type", queryset=UitDatabaseType.objects.all()),
        fk_field_spec("events__hall", "Hall", Hall.objects.all(), requires_distinct=True),
        m2m_field_spec("tags", "Tag", Tag.objects.all()),
        m2m_field_spec("genres", "Genre", Genre.objects.all()),
        datetime_field_spec("events__starts_at", "Event start"),
        text_field_spec("translations__title", "Title"),
        text_field_spec("translations__artist_name", "Artist"),
    )

    actions = (
        AddTagAction(),
        RemoveTagAction(),
        ClearTagsAction(),
        ReplaceTagsAction(),
        UpdateHallEventsAction(),
        ClearHallEventsAction(),
        DeleteEventsAction(),
        SetAttendanceModeAction(),
        SetPerformerTypeAction(),
        SetUitThemeAction(),
        SetUitTypeAction(),
    )

    def base_queryset(self):
        return (
            super()
            .base_queryset()
            .select_related("uit_database_theme", "uit_database_type", "media_gallery")
            .prefetch_related("tags")
        )
