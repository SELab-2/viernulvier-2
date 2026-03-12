"""
Models for the Events app.

Events are scheduled occurrences of productions:

    Event  ->  Production

- An **Event** links a :class:`~apps.productions.models.Production` to a
  :class:`~apps.locations.models.Hall` and defines the time window during
  which the performance takes place.
- An **EventPrice** records the ticket amount and available capacity for a
  specific :class:`~apps.pricing.models.PriceRank` within an event.

A database-level check constraint guarantees that ``ends_at >= starts_at``
for every event. The same rule is enforced at the application level via
:meth:`Event.clean`.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.core.models import BaseModel
from apps.locations.models import Hall
from apps.pricing.models import Price, PriceRank
from apps.productions.models import Production


class Event(BaseModel):
    """
    A scheduled occurrence of a production inside a hall.

    An event has a start and end time, and a set of :class:`EventPrice`
    entries that define capacity and pricing per price rank. The ``hall``
    FK is nullable to support online or location-independent events.

    The constraint ``ends_at >= starts_at`` is enforced both at the
    database level (``CheckConstraint``) and at the application level
    (:meth:`clean`), so validation fires in both the admin and the API.

    Attributes:
        production:    The production this event is a performance of.
        hall:          The hall in which the event takes place.
                       ``null`` for online or location-independent events.
        starts_at:     Date and time at which the event begins (UTC).
        ends_at:       Date and time at which the event ends (UTC).
                       Must be later or equal to ``starts_at``.
    """

    production = models.ForeignKey(
        Production,
        on_delete=models.CASCADE,
        related_name="events",
        help_text="Production this event is a performance of.",
        db_comment="The production that the event is organized for.",
    )

    hall = models.ForeignKey(
        Hall,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
        help_text="Hall in which the event takes place. `null` for online or location-independent events.",
        db_comment="The hall which the event is organized in.",
    )

    starts_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="ISO 8601 UTC datetime at which the event begins.",
        db_comment="The time at which the event starts.",
    )

    ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="ISO 8601 UTC datetime at which the event ends. Must be later or equal to `starts_at`.",
        db_comment="The time at which the event ends.",
    )

    class Meta(BaseModel.Meta):
        db_table = "event"
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(ends_at__gte=F("starts_at")) | Q(starts_at__isnull=True) | Q(ends_at__isnull=True)),
                name="event_ends_after_starts",
            )
        ]

    def clean(self) -> None:
        """
        Enforce that ``ends_at`` is later or equal to ``starts_at``.

        This mirrors the database-level ``CheckConstraint`` so that the
        validation error surfaces in the Django admin and any form-based
        flow, rather than only at the database layer.
        """
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError("Event end time cannot be before start time.")

    def __str__(self) -> str:
        production = str(self.production) if self.production else "Unknown Production"
        date = self.starts_at.strftime("%Y-%m-%d %H:%M") if self.starts_at else "TBA"
        return f"{production} @ {date}"


class EventPrice(BaseModel):
    """
    A price tier assigned to a specific event.

    Each ``EventPrice`` links an :class:`Event` to a
    :class:`~apps.pricing.models.PriceRank` and records the ticket amount
    (in euro) and the number of seats available at that rank.

    Each combination of event and price rank must be unique (enforced by a
    ``UniqueConstraint``). The ``price_rank`` FK uses ``SET_NULL`` on delete
    so that removing a rank does not cascade-delete historical pricing data.

    Attributes:
        event:       The event this price entry belongs to.
        price:       Price category for this event price entry.
                     ``null`` when the price has been deleted.
        price_rank:  The price rank availability tier.
                     ``null`` when the rank has been deleted.
        amount:      Ticket price in euro.
        available:   Number of tickets available at this rank for the event.
    """

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="prices",
        help_text="Event this price entry belongs to.",
        db_comment="The event which the price belongs to.",
    )

    price = models.ForeignKey(
        Price,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="event_prices",
        help_text="Price category for this event price entry.",
        db_comment="FK to Price.",
    )

    price_rank = models.ForeignKey(
        PriceRank,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="event_prices",
        help_text="Price rank availability tier. `null` when the rank has been deleted.",
        db_comment="The rank corresponding to the price.",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Ticket price in euro (e.g. `18.00`).",
        db_comment="The price amount.",
    )

    available = models.PositiveIntegerField(
        help_text="Number of tickets available at this price rank for the event.",
        db_comment="The amount of event tickets available for this specific price.",
    )

    class Meta(BaseModel.Meta):
        db_table = "event_price"
        verbose_name = "Event Price"
        verbose_name_plural = "Event Prices"
        ordering = ["price_rank__position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "price_rank", "price"],
                name="uniq_event_rank_price",
            )
        ]
        indexes = [
            models.Index(fields=["event"], name="idx_event_price_event"),
            models.Index(fields=["event", "price_rank", "price"], name="idx_event_rank_price"),
        ]

    def __str__(self) -> str:
        rank = str(self.price_rank) if self.price_rank else "No rank"
        return f"{self.event} - {rank} (€{self.amount})"
