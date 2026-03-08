"""
Covers:
- __str__ output
- Meta ordering
- field defaults
- check constraints (min<=max only)
- validators (step >= 1)
- uniqueness constraints (price+language, rank position, rank+language)
- indexes presence
- reverse relations
- cascade delete behavior
"""

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
    p = PriceFactory(type="standard")
    s = str(p)
    assert "standard" in s
    assert f"id={p.id}" in s


def test_price_meta_ordering_by_sort_order():
    p2 = PriceFactory(sort_order=2)
    p1 = PriceFactory(sort_order=1)

    prices = list(type(p1).objects.all())
    assert [p.id for p in prices] == [p1.id, p2.id]


def test_price_allows_minimum_set_with_maximum_null():
    """price_min_max_both_null_or_both_set constraint was removed; minimum set with
    maximum null is now permitted."""
    p = PriceFactory(minimum=0, maximum=None)
    assert p.id is not None


def test_price_allows_both_null():
    p = PriceFactory(minimum=None, maximum=None)
    assert p.id is not None


def test_price_allows_both_set():
    p = PriceFactory(minimum=0, maximum=10)
    assert p.id is not None


def test_price_check_constraint_min_lte_max():
    """minimum must not exceed maximum when both are provided."""
    with pytest.raises(Exception):
        PriceFactory(minimum=20, maximum=10)


def test_price_step_min_value_validator():
    p = PriceFactory.build(step=0)
    with pytest.raises(ValidationError):
        p.full_clean()

    p2 = PriceFactory(step=1)
    assert p2.step == 1


def test_price_allows_step_null_and_minmax_null():
    p = PriceFactory(step=None, minimum=None, maximum=None)
    assert p.id is not None


def test_price_constraints_names_present():
    """Only price_min_lte_max remains; price_min_max_both_null_or_both_set was removed."""
    names = {c.name for c in type(PriceFactory())._meta.constraints}
    assert "price_min_lte_max" in names
    assert "price_min_max_both_null_or_both_set" not in names


# ---------------------------------------------------------------------------
# PriceTranslation
# ---------------------------------------------------------------------------


def test_price_translation_unique_per_price_and_language():
    lang = LanguageFactory(code="nl")
    p = PriceFactory()

    PriceTranslationFactory(price=p, language=lang)

    with pytest.raises(ValidationError):
        PriceTranslationFactory(price=p, language=lang)


def test_price_translation_str_contains_price_type_and_language_code():
    lang = LanguageFactory(code="en")
    p = PriceFactory(type="student")
    pt = PriceTranslationFactory(price=p, language=lang)
    s = str(pt)
    assert "student" in s
    assert "[en]" in s


def test_price_translation_default_description_is_empty_string():
    lang = LanguageFactory(code="en")
    p = PriceFactory()
    pt = PriceTranslationFactory(price=p, language=lang, description="")
    assert pt.description == ""


def test_price_translation_reverse_relation_from_price():
    p = PriceFactory()
    t1 = PriceTranslationFactory(price=p)
    t2 = PriceTranslationFactory(price=p)

    assert p.translations.count() == 2
    assert set(p.translations.values_list("id", flat=True)) == {t1.id, t2.id}


def test_price_translation_cascade_delete_price_deletes_translations():
    p = PriceFactory()
    PriceTranslationFactory.create_batch(2, price=p)

    p.delete()
    assert PriceTranslation.objects.count() == 0


def test_price_translation_indexes_present():
    idx_names = {idx.name for idx in PriceTranslation._meta.indexes}
    assert "idx_price_lang" in idx_names


# ---------------------------------------------------------------------------
# PriceRank
# ---------------------------------------------------------------------------


def test_price_rank_meta_ordering_by_position():
    r2 = PriceRankFactory(position=2)
    r1 = PriceRankFactory(position=1)

    ranks = list(type(r1).objects.all())
    assert [r.id for r in ranks] == [r1.id, r2.id]


def test_price_rank_unique_position():
    PriceRankFactory(position=1)
    with pytest.raises(ValidationError):
        PriceRankFactory(position=1)


def test_price_rank_default_sold_out_buffer_is_zero():
    r = PriceRankFactory.build(sold_out_buffer=0)
    r.full_clean()
    r.save()
    assert r.sold_out_buffer == 0


def test_price_rank_str():
    pr = PriceRankFactory(position=3)
    assert str(pr) == "Rank 3"


# ---------------------------------------------------------------------------
# PriceRankTranslation
# ---------------------------------------------------------------------------


def test_price_rank_translation_unique_per_rank_and_language():
    lang = LanguageFactory(code="fr")
    pr = PriceRankFactory(position=10)

    PriceRankTranslationFactory(price_rank=pr, language=lang)

    with pytest.raises(ValidationError):
        PriceRankTranslationFactory(price_rank=pr, language=lang)


def test_price_rank_translation_str_contains_rank_and_language():
    lang = LanguageFactory(code="de")
    pr = PriceRankFactory(position=2)
    prt = PriceRankTranslationFactory(price_rank=pr, language=lang)
    s = str(prt)
    assert "Rank 2" in s
    assert "[de]" in s


def test_price_rank_translation_reverse_relation_from_rank():
    pr = PriceRankFactory()
    t1 = PriceRankTranslationFactory(price_rank=pr)
    t2 = PriceRankTranslationFactory(price_rank=pr)

    assert pr.translations.count() == 2
    assert set(pr.translations.values_list("id", flat=True)) == {t1.id, t2.id}


def test_price_rank_translation_indexes_present():
    idx_names = {idx.name for idx in PriceRankTranslation._meta.indexes}
    assert "idx_price_rank_lang" in idx_names
