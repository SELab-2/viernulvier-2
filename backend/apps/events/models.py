from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.core.model import BaseModel
from apps.locations.models import Hall
from apps.pricing.models import PriceRank
from apps.productions.models import Production


class Event(BaseModel):
    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        db_comment="The production that the event is organized for.",
        related_name="events",
    )

    hall = models.ForeignKey(
        Hall,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_comment="The hall which the event is organized in.",
        related_name="events",
    )

    starts_at = models.DateTimeField(
        db_comment="The time at which the event starts.",
        null=True,
        blank=True
        )
    ends_at = models.DateTimeField(
        db_comment="The time at which the event ends.",
        null=True,
        blank=True
        )

    ticketing_url = models.URLField(
        db_comment="The URL leading to the ticket reservations.",
        blank=True
    )

    class Meta(BaseModel.Meta):
        db_table = "event"
        verbose_name = "Event"
        verbose_name_plural = "Events"
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")),
                name="event_ends_after_starts",
            )
        ]
        ordering = ["starts_at"]

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError("Event end time must be after start time.")

class EventPrice(BaseModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        db_comment="The event which the price belongs to.",
        related_name="prices",
    )

    price_rank = models.ForeignKey(
        PriceRank,
        on_delete=models.SET_NULL,
        db_comment="The rank corresponding to the price.",
        related_name="event_prices",
        null=True,
        blank=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_comment="The price amount.",
    )

    available = models.PositiveIntegerField(
        db_comment="The amount of event tickets available for this specific price."
    )

    class Meta(BaseModel.Meta):
        db_table = "event_price"
        verbose_name = "Event Price"
        verbose_name_plural = "Event Prices"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "price_rank"],
                name="uniq_event_price_rank",
            )
        ]
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["event", "price_rank"]),
        ]
        