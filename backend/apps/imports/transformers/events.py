from .base import BaseTransformer
from ...locations.models import Hall
from ...productions.models import Production


class EventTransformer(BaseTransformer):
    def __init__(self):
        super().__init__(
            {
                # API fields to model fields
                # only ones that don't match and are present in the model
                "order_url": "ticketing_url",
            },
            {
                # Use this for foreign keys
                "production": lambda _id : self._resolve_external_id(_id, Production, ProductionTransformer()),
                "hall": lambda _id : self._resolve_external_id(_id, Hall, HallTransformer()),

                # Use other functions for custom transformations
                "ticketing_url": self._extract_url,
            }
        )
