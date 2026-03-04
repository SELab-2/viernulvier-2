from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.core.model import BaseModel
from apps.languages.models import Language


class Price(BaseModel):
    """Represents a price."""

    type = models.CharField(
        max_length=50, db_comment="Price type/category."
    )  # TODO: maybe define an enum for a limited set of price ranks

    visibility = models.CharField(
        max_length=50,
        db_comment="Visibility of the price.",
    )  # TODO: maybe define an enum for a limited set of visibility modes

    membership = models.CharField(
        max_length=50,
        db_comment="Membership requirement.",
        blank=True,
        default="",
    )

    minimum = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_comment="Minimum allowed amount (if applicable).",
    )

    maximum = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_comment="Maximum allowed amount (if applicable).",
    )

    step = models.IntegerField(
        null=True,
        blank=True,
        # TODO: determine whether minimal/maximal validator is actually needed
        validators=[MinValueValidator(1)],
        db_comment="Step size for variable pricing (if applicable).",
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        db_comment="Ordering index for displaying prices.",
    )

    cineville_box = models.BooleanField(
        default=False,
        db_comment="Whether this price is for Cineville box.",
    )

    class Meta(BaseModel.Meta):
        db_table = "price"
        verbose_name = "Price"
        verbose_name_plural = "Prices"
        ordering = ["sort_order"]
        constraints = [
            models.CheckConstraint(
                condition=Q(minimum__isnull=True, maximum__isnull=True)
                | Q(minimum__isnull=False, maximum__isnull=False),
                name="price_min_max_both_null_or_both_set",
            ),
            models.CheckConstraint(
                condition=Q(minimum__isnull=True, maximum__isnull=True)
                | Q(minimum__lte=F("maximum")),
                name="price_min_lte_max",
            ),
        ]

    def __str__(self):
        return f"{self.type} (id={self.id})"


class PriceTranslation(BaseModel):
    """Represents the translation of a price."""

    price = models.ForeignKey(
        Price,
        on_delete=models.CASCADE,
        db_comment="The price that this is a translation of.",
        related_name="translations",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        db_comment="The language that corresponds to the translation.",
        related_name="price_translations",
    )

    description = models.CharField(
        max_length=255,
        db_comment="Description of the price translation.",
        blank=True,
        default="",
    )

    class Meta(BaseModel.Meta):
        db_table = "price_translation"
        verbose_name = "Price Translation"
        verbose_name_plural = "Price Translations"
        constraints = [
            models.UniqueConstraint(
                fields=["price", "language"], name="unique_price_language"
            )
        ]
        indexes = [
            models.Index(fields=["price", "language"], name="idx_price_lang"),
        ]

    def __str__(self):
        return f"{self.price.type} [{self.language.code}]"


class PriceRank(BaseModel):
    """Represents a price rank."""

    position = models.PositiveIntegerField(
        db_comment="Rank position used for ordering/priority.",
    )

    sold_out_buffer = models.PositiveIntegerField(
        default=0,
        db_comment="Extra buffer used to consider rank sold out earlier/later.",
    )

    class Meta(BaseModel.Meta):
        db_table = "price_rank"
        verbose_name = "Price Rank"
        verbose_name_plural = "Price Ranks"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["position"], name="uniq_price_rank_position"
            ),
        ]

    def __str__(self):
        return f"Rank {self.position}"


class PriceRankTranslation(BaseModel):
    """Represents the translation of a price rank."""

    price_rank = models.ForeignKey(
        PriceRank,
        on_delete=models.CASCADE,
        db_comment="The price rank that this is a translation of.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="pricerank_translations",
        db_comment=
            "The language that corresponds to the translation of the price rank.",
    )

    description = models.CharField(
        max_length=255,
        db_comment="Description of the price rank translation.",
        blank=True,
        default="",
    )

    class Meta(BaseModel.Meta):
        db_table = "price_rank_translation"
        verbose_name = "Price Rank Translation"
        verbose_name_plural = "Price Rank Translations"
        constraints = [
            models.UniqueConstraint(
                fields=["price_rank", "language"], name="unique_price_rank_language"
            )
        ]
        indexes = [
            models.Index(fields=["price_rank", "language"], name="idx_price_rank_lang"),
        ]

    def __str__(self):
        return f"{self.price_rank} [{self.language.code}]"
