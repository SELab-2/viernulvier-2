"""
Models for the Pricing app.

Pricing is split across two independent hierarchies:

    Price  ->  PriceTranslation
    PriceRank  ->  PriceRankTranslation

- A **Price** defines a ticket price category (e.g. full price, student,
  Cineville) with optional variable-pricing constraints.
- A **PriceRank** defines an ordered availability tier that controls when
  a price level is considered sold out.

Both models have companion ``*Translation`` models for localised descriptions.
"""

from django.db import models
from django.db.models import F, Q
from django.core.validators import MinValueValidator

from apps.core.models import BaseModel
from apps.languages.models import Language


class Price(BaseModel):
    """
    A ticket price category.

    Prices are typed (e.g. ``full``, ``student``) and carry visibility and
    membership rules. Variable pricing is supported via the ``minimum``,
    ``maximum``, and ``step`` fields — either all three are set or all three
    are ``null``.

    Attributes:
        type:          Internal identifier for the price category.
        visibility:    Controls which audiences see this price.
        membership:    Optional membership requirement (empty string = none).
        minimum:       Lower bound for variable pricing (inclusive).
        maximum:       Upper bound for variable pricing (inclusive).
        step:          Increment size for variable pricing.
        sort_order:    Display order; lower values appear first.
        cineville_box: ``True`` when this price applies to Cineville box holders.
    """

    type = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Internal identifier for the price category (e.g. `full`, `student`).",
        db_comment="Price type / category.",
    )

    visibility = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        help_text="Controls which audiences see this price (e.g. `public`, `members_only`).",
        db_comment="Visibility of the price.",
    )

    membership = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Membership level required to access this price. Empty string means no requirement.",
        db_comment="Membership requirement for the price.",
    )

    minimum = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Lower bound for variable pricing in euro cents (inclusive). "
            "Must be set together with `maximum` and `step`, or left null."
        ),
        db_comment="Minimum allowed amount for variable pricing.",
    )

    maximum = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Upper bound for variable pricing in euro cents (inclusive). "
            "Must be set together with `minimum` and `step`, or left null."
        ),
        db_comment="Maximum allowed amount for variable pricing.",
    )

    step = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=(
            "Increment size in euro cents for variable pricing. "
            "Must be ≥ 1. Must be set together with `minimum` and `maximum`, or left null."
        ),
        db_comment="Step size for variable pricing.",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order index. Lower values appear first.",
        db_comment="Ordering index for displaying prices.",
    )

    cineville_box = models.BooleanField(
        default=False,
        help_text="`true` when this price applies to Cineville box holders.",
        db_comment="Whether this price is for Cineville box.",
    )

    class Meta(BaseModel.Meta):
        db_table = "price"
        verbose_name = "Price"
        verbose_name_plural = "Prices"
        ordering = ["sort_order", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(minimum__isnull=True, maximum__isnull=True)
                    | Q(minimum__lte=F("maximum"))
                ),
                name="price_min_lte_max",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.type} (id={self.id})"


class PriceTranslation(BaseModel):
    """
    Localised description for a Price.

    Each price can have at most one translation per language.

    Attributes:
        price:       The price this translation belongs to.
        language:    The language of this translation.
        description: Localised human-readable label for the price.
    """

    price = models.ForeignKey(
        Price,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Price this translation belongs to.",
        db_comment="FK to Price.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="price_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Localised human-readable label for this price (e.g. `Full price`, `Student`).",
        db_comment="Translated description of the price.",
    )

    class Meta(BaseModel.Meta):
        db_table = "price_translation"
        verbose_name = "Price Translation"
        verbose_name_plural = "Price Translations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["price", "language"],
                name="unique_price_language",
            )
        ]
        indexes = [
            models.Index(fields=["price", "language"], name="idx_price_lang"),
        ]

    def __str__(self) -> str:
        return f"{self.price.type} [{self.language.code}]"


class PriceRank(BaseModel):
    """
    An ordered availability tier for pricing.

    Price ranks control when a price level is considered sold out.
    A ``sold_out_buffer`` allows a rank to be marked sold out slightly
    earlier or later than its actual capacity.

    Attributes:
        position:        Rank position; lower values have higher priority.
        sold_out_buffer: Extra capacity offset for sold-out determination.
    """

    position = models.PositiveIntegerField(
        null=False,
        blank=False,
        help_text="Rank position used for ordering and priority. Must be unique.",
        db_comment="Rank position used for ordering / priority.",
    )

    sold_out_buffer = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Extra capacity offset used to consider this rank sold out "
            "slightly earlier (positive) or later (negative) than actual capacity."
        ),
        db_comment="Extra buffer for sold-out determination.",
    )

    class Meta(BaseModel.Meta):
        db_table = "price_rank"
        verbose_name = "Price Rank"
        verbose_name_plural = "Price Ranks"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["position"],
                name="uniq_price_rank_position",
            )
        ]

    def __str__(self) -> str:
        return f"Rank {self.position}"


class PriceRankTranslation(BaseModel):
    """
    Localised description for a PriceRank.

    Each price rank can have at most one translation per language.

    Attributes:
        price_rank:  The price rank this translation belongs to.
        language:    The language of this translation.
        description: Localised human-readable label for the rank.
    """

    price_rank = models.ForeignKey(
        PriceRank,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Price rank this translation belongs to.",
        db_comment="FK to PriceRank.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="pricerank_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Localised human-readable label for this price rank.",
        db_comment="Translated description of the price rank.",
    )

    class Meta(BaseModel.Meta):
        db_table = "price_rank_translation"
        verbose_name = "Price Rank Translation"
        verbose_name_plural = "Price Rank Translations"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["price_rank", "language"],
                name="unique_price_rank_language",
            )
        ]
        indexes = [
            models.Index(fields=["price_rank", "language"], name="idx_price_rank_lang"),
        ]

    def __str__(self) -> str:
        return f"{self.price_rank} [{self.language.code}]"