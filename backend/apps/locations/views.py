"""
ViewSets for the Locations app.

Schema annotations are kept in schemas.py so this file stays focused
on routing and queryset configuration only.
"""

from apps.core.cache_mixin import cache_read_actions
from apps.core.views import ApiModelViewSet

from .filters import HallFilter, LocationFilter, SpaceFilter
from .models import Hall, Location, Space
from .schemas import extend_schema, hall_schema, location_schema, space_schema
from .serializers import HallSerializer, LocationSerializer, SpaceSerializer

_TAG = "Locations"


@cache_read_actions()
@extend_schema(tags=[_TAG])
@location_schema
class LocationViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Location objects.

    A location represents a physical venue or address. It is the top of the
    three-level hierarchy: Location -> Space -> Hall.

    Translated fields (e.g. ``name``) return all available translations as a
    language-code dictionary. Translations are managed via the dedicated
    Location Translation endpoints.

    Filtering
    ---------
    ``?city=gent``
        Substring match on the city name.
    ``?country=BE``
        Exact country code match (case-insensitive).
    ``?postal_code=9000``
        Exact postal code match.
    ``?is_own_location=true``
        Only venues owned or operated by the organisation.
    ``?name=stadsschouwburg``
        Substring match across all translated location names.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=city`` / ``?ordering=-city``
        Alphabetical by city.
    ``?ordering=country`` / ``?ordering=-country``
        Alphabetical by country.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=gent``
        Full-text search across ``city``, ``country``, ``street``,
        and translated names.
    """

    queryset = Location.objects.prefetch_related("translations__language").order_by("id").distinct()
    serializer_class = LocationSerializer

    filterset_class = LocationFilter
    ordering_fields = ["id", "city", "country", "postal_code"]
    ordering = ["id"]
    search_fields = ["city", "country", "street", "translations__name"]


@cache_read_actions()
@extend_schema(tags=[_TAG])
@space_schema
class SpaceViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Space objects.

    A space is a distinct physical area (building, wing, …) within a location.
    It groups one or more halls.

    Filtering
    ---------
    ``?location=3``
        Spaces belonging to a specific location.
    ``?name=foyer``
        Substring match across all translated space names.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=location`` / ``?ordering=-location``
        Group by parent location FK.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=studio``
        Full-text search across translated space names.
    """

    queryset = (
        Space.objects.select_related("location")
        .prefetch_related(
            "translations__language",
            "location__translations__language",
            "halls__translations__language",
        )
        .order_by("id")
    )
    serializer_class = SpaceSerializer

    filterset_class = SpaceFilter
    ordering_fields = ["id", "location"]
    ordering = ["id"]
    search_fields = ["translations__name"]


@cache_read_actions()
@extend_schema(tags=[_TAG])
@hall_schema
class HallViewSet(ApiModelViewSet):
    """
    CRUD endpoints for Hall objects.

    A hall is a specific room or auditorium within a space. It carries
    seating configuration flags and supports localised ``name`` and
    ``remark`` fields.

    Filtering
    ---------
    ``?space=2``
        Halls belonging to a specific space.
    ``?location=1``
        Halls in any space belonging to a specific location.
    ``?seat_selection=true``
        Only halls that allow seat selection.
    ``?open_seating=true``
        Only halls with general-admission seating.
    ``?name=grote+zaal``
        Substring match across all translated hall names.
    ``?external_id=abc``
        Exact match on the external identifier.

    Ordering
    --------
    ``?ordering=space`` / ``?ordering=-space``
        Group by parent space FK.
    ``?ordering=id`` / ``?ordering=-id``
        By creation order (default ascending).

    Search
    ------
    ``?search=zaal``
        Full-text search across translated hall names and remarks.
    """

    queryset = (
        Hall.objects.select_related("space", "space__location")
        .prefetch_related(
            "translations__language",
            "space__translations__language",
            "space__location__translations__language",
        )
        .order_by("id")
    )
    serializer_class = HallSerializer

    filterset_class = HallFilter
    ordering_fields = ["id", "space"]
    ordering = ["id"]
    search_fields = ["translations__name", "translations__remark"]
