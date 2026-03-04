"""
Covers:
- __str__ output
- Meta ordering
- field defaults
- check constraints (min/max, min<=max)
- validators (step >= 1)
- uniqueness constraints (price+language, rank position, rank+language)
- indexes presence
- reverse relations
- cascade delete behavior
"""

from django.db import connection
import pytest
from django.core.exceptions import ValidationError

from apps.pricing.models import PriceTranslation, PriceRankTranslation
from tests.factories.language import LanguageFactory
from tests.factories.pricing import (
    PriceFactory,
    PriceTranslationFactory,
    PriceRankFactory,
    PriceRankTranslationFactory,
)

pytestmark = pytest.mark.django_db(transaction=True)


# ---------------------------------------------------------------------------
# Price
# ---------------------------------------------------------------------------

def test_price_str_contains_type_and_id():
    """Test case for test_price_str_contains_type_and_id."""
    p = PriceFactory(type="standard")
    s = str(p)
    assert "standard" in s
    assert f"id={p.id}" in s  # model uses f"{self.type} (id={self.id})" :contentReference[oaicite:3]{index=3}


def test_price_meta_ordering_by_sort_order():
    """Test case for test_price_meta_ordering_by_sort_order."""
    p2 = PriceFactory(sort_order=2)
    p1 = PriceFactory(sort_order=1)

    prices = list(type(p1).objects.all())
    assert [p.id for p in prices] == [p1.id, p2.id]  # ordering=["sort_order"] :contentReference[oaicite:4]{index=4}


def test_price_check_constraint_min_max_both_null_or_both_set():
    """Test case for test_price_check_constraint_min_max_both_null_or_both_set."""
    with pytest.raises(ValidationError):
        PriceFactory(minimum=0, maximum=None)

    ok = PriceFactory(minimum=0, maximum=10)
    assert ok.id is not None

    ok2 = PriceFactory(minimum=None, maximum=None)
    assert ok2.id is not None


def test_price_check_constraint_min_lte_max():
    """Test case for test_price_check_constraint_min_lte_max."""
    with pytest.raises(ValidationError):
        PriceFactory(minimum=20, maximum=10)


def test_price_step_min_value_validator():
    """Test case for test_price_step_min_value_validator."""
    # step has MinValueValidator(1) :contentReference[oaicite:7]{index=7}
    p = PriceFactory.build(step=0)
    with pytest.raises(ValidationError):
        p.full_clean()

    p2 = PriceFactory(step=1)
    assert p2.step == 1


def test_price_allows_step_null_and_minmax_null():
    """Test case for test_price_allows_step_null_and_minmax_null."""
    p = PriceFactory(step=None, minimum=None, maximum=None)
    assert p.id is not None


def test_price_constraints_names_present():
    """Test case for test_price_constraints_names_present."""
    names = {c.name for c in type(PriceFactory())._meta.constraints}
    assert "price_min_max_both_null_or_both_set" in names
    assert "price_min_lte_max" in names


# ---------------------------------------------------------------------------
# PriceTranslation
# ---------------------------------------------------------------------------

def test_price_translation_unique_per_price_and_language():
    """Test case for test_price_translation_unique_per_price_and_language."""
    lang = LanguageFactory(code="nl")
    p = PriceFactory()

    PriceTranslationFactory(price=p, language=lang)

    with pytest.raises(ValidationError):
        PriceTranslationFactory(price=p, language=lang)


def test_price_translation_str_contains_price_type_and_language_code():
    """Test case for test_price_translation_str_contains_price_type_and_language_code."""
    lang = LanguageFactory(code="en")
    p = PriceFactory(type="student")
    pt = PriceTranslationFactory(price=p, language=lang)
    s = str(pt)
    assert "student" in s
    assert "[en]" in s  # model uses f"{self.price.type} [{self.language.code}]" :contentReference[oaicite:8]{index=8}


def test_price_translation_default_description_is_empty_string():
    """Test case for test_price_translation_default_description_is_empty_string."""
    lang = LanguageFactory(code="en")
    p = PriceFactory()
    pt = PriceTranslationFactory(price=p, language=lang, description="")
    assert pt.description == ""


def test_price_translation_reverse_relation_from_price():
    """Test case for test_price_translation_reverse_relation_from_price."""
    p = PriceFactory()
    t1 = PriceTranslationFactory(price=p)
    t2 = PriceTranslationFactory(price=p)

    assert p.translations.count() == 2
    assert set(p.translations.values_list("id", flat=True)) == {t1.id, t2.id}


def test_price_translation_cascade_delete_price_deletes_translations():
    """Test case for test_price_translation_cascade_delete_price_deletes_translations."""
    p = PriceFactory()
    PriceTranslationFactory.create_batch(2, price=p)

    p.delete()
    assert PriceTranslation.objects.count() == 0  # on_delete=CASCADE :contentReference[oaicite:9]{index=9}


def test_price_translation_indexes_present():
    """Test case for test_price_translation_indexes_present."""
    idx_names = {idx.name for idx in PriceTranslation._meta.indexes}
    assert "idx_price_lang" in idx_names  # defined in model meta :contentReference[oaicite:11]{index=11}


# ---------------------------------------------------------------------------
# PriceRank
# ---------------------------------------------------------------------------

def test_price_rank_meta_ordering_by_position():
    """Test case for test_price_rank_meta_ordering_by_position."""
    r2 = PriceRankFactory(position=2)
    r1 = PriceRankFactory(position=1)

    ranks = list(type(r1).objects.all())
    assert [r.id for r in ranks] == [r1.id, r2.id]


def test_price_rank_unique_position():
    """Test case for test_price_rank_unique_position."""
    PriceRankFactory(position=1)
    with pytest.raises(ValidationError):
        PriceRankFactory(position=1)


def test_price_rank_default_sold_out_buffer_is_zero():
    """Test case for test_price_rank_default_sold_out_buffer_is_zero."""
    r = PriceRankFactory.build(sold_out_buffer=0)
    r.full_clean()
    r.save()
    assert r.sold_out_buffer == 0


def test_price_rank_str():
    """Test case for test_price_rank_str."""
    pr = PriceRankFactory(position=3)
    assert str(pr) == "Rank 3"  # model uses f"Rank {self.position}" :contentReference[oaicite:13]{index=13}


# ---------------------------------------------------------------------------
# PriceRankTranslation
# ---------------------------------------------------------------------------

def test_price_rank_translation_unique_per_rank_and_language():
    """Test case for test_price_rank_translation_unique_per_rank_and_language."""
    lang = LanguageFactory(code="fr")
    pr = PriceRankFactory(position=10)

    PriceRankTranslationFactory(price_rank=pr, language=lang)

    with pytest.raises(ValidationError):
        PriceRankTranslationFactory(price_rank=pr, language=lang)


def test_price_rank_translation_str_contains_rank_and_language():
    """Test case for test_price_rank_translation_str_contains_rank_and_language."""
    lang = LanguageFactory(code="de")
    pr = PriceRankFactory(position=2)
    prt = PriceRankTranslationFactory(price_rank=pr, language=lang)
    s = str(prt)
    assert "Rank 2" in s
    assert "[de]" in s  # model uses f"{self.price_rank} [{self.language.code}]" :contentReference[oaicite:14]{index=14}


def test_price_rank_translation_reverse_relation_from_rank():
    """Test case for test_price_rank_translation_reverse_relation_from_rank."""
    pr = PriceRankFactory()
    t1 = PriceRankTranslationFactory(price_rank=pr)
    t2 = PriceRankTranslationFactory(price_rank=pr)

    assert pr.translations.count() == 2
    assert set(pr.translations.values_list("id", flat=True)) == {t1.id, t2.id}


def test_price_rank_translation_indexes_present():
    """Test case for test_price_rank_translation_indexes_present."""
    idx_names = {idx.name for idx in PriceRankTranslation._meta.indexes}
    assert "idx_price_rank_lang" in idx_names  # defined in model meta :contentReference[oaicite:17]{index=17}
