"""
ViewSets for the Locations app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.views import ApiModelViewSet

from .models import Hall, Location, Space
from .schemas import extend_schema, hall_schema, location_schema, space_schema
from .serializers import HallSerializer, LocationSerializer, SpaceSerializer

_TAG = (
    "Locations"  # Reusable tag for all location-related endpoints in the OpenAPI docs
)


@extend_schema(tags=[_TAG])
@location_schema
class LocationViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Location objects.

    A location represents a physical venue or address. It is the top of
    the three-level hierarchy: Location → Space → Hall.

    Translated fields (e.g. `name`) return all available translations
    as a dictionary (e.g. {"en": "City Hall", "fr": "Hôtel de Ville"}).
    Translations are managed via the Location Translation endpoints.
    """

    queryset = (
        Location.objects.prefetch_related("translations__language").order_by("id").all()
    )
    serializer_class = LocationSerializer


@extend_schema(tags=[_TAG])
@space_schema
class SpaceViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Space objects.

    A space is a distinct physical area (building, wing, …) within a location.
    It groups one or more halls.

    Prefetches translations and the owning location to avoid N+1 queries when
    rendering translated fields and related lookups.
    """

    queryset = (
        Space.objects.select_related("location")
        .prefetch_related("translations__language")
        .order_by("id")
        .all()
    )
    serializer_class = SpaceSerializer


@extend_schema(tags=[_TAG])
@hall_schema
class HallViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Hall objects.

    A hall is a specific room or auditorium within a space. It carries
    seating configuration flags and supports localised `name` and `remark`
    fields.

    Prefetches translations and selects the related space and location so
    hall listings remain efficient even when translated fields are rendered.
    """

    queryset = (
        Hall.objects.select_related("space", "space__location")
        .prefetch_related("translations__language")
        .order_by("id")
        .all()
    )
    serializer_class = HallSerializer
