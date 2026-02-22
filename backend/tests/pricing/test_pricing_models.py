import pytest
from django.db import IntegrityError

from tests.factories.language import LanguageFactory
from tests.factories.pricing import (
    PriceFactory,
    PriceTranslationFactory,
    PriceRankFactory,
    PriceRankTranslationFactory,
)

pytestmark = pytest.mark.django_db(transaction=True)


def test_price_str():
    p = PriceFactory(type="standard")
    assert "standard" in str(p)


def test_price_default_ordering_by_sort_order():
    p2 = PriceFactory(sort_order=2)
    p1 = PriceFactory(sort_order=1)

    prices = list(type(p1).objects.all())
    assert prices[0].id == p1.id
    assert prices[1].id == p2.id


def test_price_check_constraint_min_max_both_null_or_both_set():
    with pytest.raises(IntegrityError):
        PriceFactory(minimum=0, maximum=None)

    p = PriceFactory(minimum=0, maximum=10)
    assert p.id is not None

    p = PriceFactory(minimum=None, maximum=None)
    assert p.id is not None


def test_price_check_constraint_min_lte_max():
    # minimum > maximum => moet falen
    with pytest.raises(IntegrityError):
        PriceFactory(minimum=20, maximum=10)


def test_price_translation_unique_per_price_and_language():
    lang = LanguageFactory(code="nl")
    p = PriceFactory()

    PriceTranslationFactory(price=p, language=lang)

    with pytest.raises(IntegrityError):
        PriceTranslationFactory(price=p, language=lang)


def test_price_translation_str_contains_price_type_and_language_code():
    lang = LanguageFactory(code="en")
    p = PriceFactory(type="student")
    pt = PriceTranslationFactory(price=p, language=lang)
    assert "student" in str(pt)
    assert "[en]" in str(pt)


def test_price_rank_unique_position():
    PriceRankFactory(position=1)

    with pytest.raises(IntegrityError):
        PriceRankFactory(position=1)


def test_price_rank_str():
    pr = PriceRankFactory(position=3)
    assert str(pr) == "Rank 3"


def test_price_rank_translation_unique_per_rank_and_language():
    lang = LanguageFactory(code="fr")
    pr = PriceRankFactory(position=10)

    PriceRankTranslationFactory(price_rank=pr, language=lang)

    with pytest.raises(IntegrityError):
        PriceRankTranslationFactory(price_rank=pr, language=lang)


def test_price_rank_translation_str_contains_rank_and_language():
    lang = LanguageFactory(code="de")
    pr = PriceRankFactory(position=2)
    prt = PriceRankTranslationFactory(price_rank=pr, language=lang)
    assert "Rank 2" in str(prt)
    assert "[de]" in str(prt)