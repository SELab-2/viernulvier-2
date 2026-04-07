"""Contract tests for sync_viernulvier model/config wiring."""

import pytest

from apps.genres.models import GenreUseAs
from apps.imports.management.commands.sync_viernulvier import PRODUCTION_CONFIG, SYNC_STEPS
from apps.imports.management.commands.sync_viernulvier import (
    _is_not_longterm,
    _resolve_genre_use_as,
    nee_ja_to_bool,
)
from apps.imports.scrapers.viernulvier import M2MConfig, ModelSyncConfig, TranslationConfig

from ._sync_configs_helpers import (
    ALL_CONFIGS,
    BASE_CONFIGS,
    CONFIGS_AND_MODELS,
    CONFIGS_WITH_TRANSLATIONS,
    DEFINED_CONFIGS,
    EXTERNAL_ID_CONFIGS,
    FK_RESOLVER_CONFIGS,
    M2M_REQUIRED_ATTRIBUTES,
    REQUIRED_CONFIG_ATTRIBUTES,
    SYNC_STEP_ENDPOINTS,
    SYNC_STEP_NAMES,
    TRANSLATION_REQUIRED_ATTRIBUTES,
    VALUE_TRANSFORM_CONFIGS,
    get_model_field_names,
)


def test_all_configs_are_model_sync_config() -> None:
    for config in ALL_CONFIGS:
        assert isinstance(config, ModelSyncConfig)


def test_configs_have_required_base_attributes() -> None:
    for config in BASE_CONFIGS:
        assert isinstance(config.field_map, dict)
        assert hasattr(config, "lookup_field")
        assert hasattr(config, "api_id_key")


def test_configs_with_translations_have_valid_structure() -> None:
    for config in CONFIGS_WITH_TRANSLATIONS:
        assert isinstance(config.translations, list)
        for trans_cfg in config.translations:
            assert isinstance(trans_cfg, TranslationConfig)
            for attr in TRANSLATION_REQUIRED_ATTRIBUTES:
                assert hasattr(trans_cfg, attr)


def test_production_config_has_valid_m2m() -> None:
    assert isinstance(PRODUCTION_CONFIG.m2m, list)
    assert PRODUCTION_CONFIG.m2m

    for m2m_cfg in PRODUCTION_CONFIG.m2m:
        assert isinstance(m2m_cfg, M2MConfig)
        for attr in M2M_REQUIRED_ATTRIBUTES:
            assert hasattr(m2m_cfg, attr)


def test_all_mapped_fields_exist_in_models() -> None:
    for config, model in CONFIGS_AND_MODELS:
        model_fields = get_model_field_names(model)

        for api_field, model_field in config.field_map.items():
            if model_field is None:
                continue
            field_exists = model_field in model_fields or f"{model_field}_id" in model_fields
            assert field_exists, (
                f"Config for {model.__name__}: mapped field '{model_field}' "
                f"(from API field '{api_field}') doesn't exist in model"
            )


def test_value_transforms_reference_model_fields() -> None:
    for config, model in VALUE_TRANSFORM_CONFIGS:
        model_fields = get_model_field_names(model)
        for field_name in config.value_transforms:
            assert field_name in model_fields, (
                f"Config for {model.__name__}: value_transform field '{field_name}' doesn't exist in model"
            )


def test_fk_resolvers_reference_model_fields() -> None:
    for config, model in FK_RESOLVER_CONFIGS:
        model_fields = get_model_field_names(model)
        for field_name in config.fk_resolvers:
            assert field_name in model_fields, (
                f"Config for {model.__name__}: fk_resolver field '{field_name}' doesn't exist in model"
            )


def test_sync_steps_structure_and_uniqueness() -> None:
    assert isinstance(SYNC_STEPS, list)
    assert SYNC_STEPS

    for step in SYNC_STEPS:
        assert isinstance(step, tuple)
        assert len(step) == 4

        name, model, config, endpoint = step
        assert isinstance(name, str)
        assert hasattr(model, "_meta")
        assert isinstance(config, ModelSyncConfig)
        assert isinstance(endpoint, str)
        assert endpoint.startswith("/")

    assert len(SYNC_STEP_NAMES) == len(set(SYNC_STEP_NAMES)), "Duplicate sync step names found"
    assert len(SYNC_STEP_ENDPOINTS) == len(set(SYNC_STEP_ENDPOINTS)), "Duplicate sync step endpoints found"


def test_sync_steps_match_defined_configs() -> None:
    configs_in_steps = [config for _, _, config, _ in SYNC_STEPS]

    for config in DEFINED_CONFIGS:
        assert config in configs_in_steps, f"Config {config} is defined but not used in SYNC_STEPS"

    assert len(configs_in_steps) == len(DEFINED_CONFIGS), (
        f"SYNC_STEPS has {len(configs_in_steps)} configs but {len(DEFINED_CONFIGS)} are defined"
    )


def test_sync_step_models_have_external_id() -> None:
    for name, model, _config, _endpoint in SYNC_STEPS:
        model_fields = get_model_field_names(model)
        assert "external_id" in model_fields, f"Model {model.__name__} used in sync step '{name}' has no external_id"


def test_configs_map_external_id() -> None:
    for name, model, config in EXTERNAL_ID_CONFIGS:
        model_fields = get_model_field_names(model)
        assert "external_id" in model_fields, f"Model {name} has no external_id field"

        if "@id" in config.field_map:
            assert config.field_map["@id"] == "external_id", f"Config for {name} doesn't map '@id' to 'external_id'"


def test_configs_expose_required_sync_attributes() -> None:
    for _name, _model, config, _endpoint in SYNC_STEPS:
        for attr in REQUIRED_CONFIG_ATTRIBUTES:
            assert hasattr(config, attr), f"Config {config} missing required attribute '{attr}'"


def test_lookup_field_exists_in_all_models() -> None:
    for _name, model, config, _endpoint in SYNC_STEPS:
        model_fields = get_model_field_names(model)
        assert config.lookup_field in model_fields, (
            f"Model {model.__name__} doesn't have lookup_field '{config.lookup_field}'"
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ja", True),
        ("JA", True),
        ("  ja  ", True),
        ("true", True),
        ("yes", True),
        ("1", True),
        ("TRUE", True),
        (" YES ", True),
        (" 1 ", True),
        ("nee", False),
        ("NEE", False),
        ("  nee  ", False),
        ("false", False),
        ("no", False),
        ("0", False),
        ("FALSE", False),
        (" NO ", False),
        (" 0 ", False),
        ("", False),
        ("   ", False),
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (42, True),
        (-1, True),
        (None, False),
        ([], False),
        ([1, 2], True),
        ({}, False),
        ({"x": 1}, True),
    ],
)
def test_nee_ja_to_bool(value, expected) -> None:
    """nee_ja_to_bool should support nl/en strings, bools, ints, and fallback coercion."""
    assert nee_ja_to_bool(value) is expected


@pytest.mark.django_db
def test_resolve_genre_use_as_creates_new() -> None:
    """When no matching row exists, _resolve_genre_use_as creates one."""
    pk = _resolve_genre_use_as("test_genre")
    assert pk is not None
    assert GenreUseAs.objects.filter(pk=pk, name="test_genre").exists()


@pytest.mark.django_db
def test_resolve_genre_use_as_returns_existing() -> None:
    """When a matching row exists, _resolve_genre_use_as returns its pk."""
    existing = GenreUseAs.objects.create(name="existing_genre")
    pk = _resolve_genre_use_as("existing_genre")

    assert pk == existing.pk
    assert GenreUseAs.objects.filter(name="existing_genre").count() == 1


@pytest.mark.django_db
def test_resolve_genre_use_as_handles_none() -> None:
    """None input resolves to the default 'unknown' row."""
    pk = _resolve_genre_use_as(None)
    assert pk is not None
    assert GenreUseAs.objects.filter(pk=pk, name="unknown").exists()


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"production": {"@id": "/api/v1/productions/123"}}, True),
        ({"production": {"@id": "/api/v1/longterm/456"}}, False),
        ({"production": "/api/v1/productions/99"}, True),
        ({"production": "/api/v1/longterm/99"}, False),
        ({}, True),
        ({"production": None}, True),
    ],
)
def test_is_not_longterm(payload, expected) -> None:
    """_is_not_longterm should only reject payloads pointing to /longterm/ productions."""
    assert _is_not_longterm(payload) is expected

