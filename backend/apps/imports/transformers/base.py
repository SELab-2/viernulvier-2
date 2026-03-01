from typing import Any, Callable, Dict, Type

from apps.core.models import BaseModel
from apps.imports.scrapers.viernulvier import sync_viernulvier


class BaseTransformer:
    """Transformeert ruwe API-data naar model-compatibele velden.

    Subclasses definiëren:
        field_map: hernoem API-velden naar modelvelden
            {"api_field": "model_field"}
        transform_funcs: pas een waarde aan na het hernoemen
            {"model_field": callable}
    """

    def __init__(self, field_map: Dict[str, str], transform_funcs: Dict[str, Callable[[Any], Any]]):
        self.field_map = field_map
        self.transform_funcs = transform_funcs

        self.field_map["@id"] = "external_id"

    def transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single API item into a model-compatible dict.

        Steps:
            1. Rename fields via field_map.
            2. Apply transform_funcs to renamed fields.
            3. Unknown fields are passed through as-is.

        Args:
            item: Raw API response dict.

        Returns:
            Transformed dict ready for update_or_create.
        """
        result = {}

        for api_key, value in item.items():
            model_key = self.field_map.get(api_key, api_key)
            result[model_key] = value

        for model_key, func in self.transform_funcs.items():
            if model_key in result:
                result[model_key] = func(result[model_key])

        return result

    @staticmethod
    def _resolve_external_id(data: str | dict, model: Type[BaseModel], transformer: BaseTransformer) -> BaseModel:
        """Search for or create an object based on external ID.

        Args:
            data: The external ID as received from the API or a dictionary with the full item data.
            model: The Django model class to query (e.g., Hall).

        Returns:
            The primary key of the object, or None if external_id is empty.
        """
        if isinstance(data, dict):
            external_id = data.get("@id", "")
        else:
            external_id = data

        try:
            obj = model.objects.get(external_id=external_id)
        except model.DoesNotExist:
            endpoint = external_id.split("/api/v1/")[1]
            sync_viernulvier(model, transformer, endpoint)
            try:
                obj = model.objects.get(external_id=external_id)
            except model.DoesNotExist:
                raise ValueError(f"Object with external_id '{external_id}' not found after sync.")

        return obj

    @staticmethod
    def _extract_url(value: dict | str | None) -> str:
        """Haal de best beschikbare URL op uit een meertalig dict of string.

        Args:
            value: Dict met taalcodes als keys, of een gewone URL-string.

        Returns:
            Een URL-string, of lege string als niets gevonden.
        """
        if isinstance(value, dict):
            return value.get("nl") or value.get("fr") or next(iter(value.values()), "")
        return value or ""
