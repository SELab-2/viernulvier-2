from django.db import models
from django.db.models import Q, F
from apps.core.model import BaseModel


class Event(BaseModel):
    production = models.ForeignKey(
        Production, # TO DO: implement Production model
        on_delete=models.CASCADE,
        db_comment="The production that the event is organized for.",
        related_name="events",
    )

    hall = models.ForeignKey(
        Hall, # TO DO: implement Hall model
        on_delete=models.PROTECT,
        db_comment="The hall which the event is organized in.",
        related_name="events",
    )

    starts_at = models.DateTimeField(db_comment="The time at which the event starts.")
    ends_at = models.DateTimeField(db_comment="The time at which the event ends.")

    ticketing_url = models.URLField(
        db_comment="The URL leading to the ticket reservations.",
        blank=True,
        null=True,
    )

    class Meta(BaseModel.Meta):
        db_table = "event"
        verbose_name = "Event"
        verbose_name_plural = "Events"
        constraints = [
            models.CheckConstraint(
                check=Q(ends_at__gt=F("starts_at")),
                name="event_ends_after_starts",
            )
        ]
        