"""ViewSets for location-related models with API-key access control."""

from apps.core.views import ApiModelViewSet
from .models import Hall, Location, Space
from .serializers import HallSerializer, LocationSerializer, SpaceSerializer


class LocationViewSet(ApiModelViewSet):
	"""API endpoint for locations with translated names.

	Access rules:
		- Public API key -> read-only
		- Internal API key -> full CRUD
	"""

	queryset = (
		Location.objects.prefetch_related("translations__language")
		.order_by("id")
		.all()
	)
	serializer_class = LocationSerializer


class SpaceViewSet(ApiModelViewSet):
	"""API endpoint for spaces.

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


class HallViewSet(ApiModelViewSet):
	"""API endpoint for halls.

	Prefetches translations and selects related space/location so hall listings
	stay efficient even with translated fields.
	"""

	queryset = (
		Hall.objects.select_related("space", "space__location")
		.prefetch_related("translations__language")
		.order_by("id")
		.all()
	)
	serializer_class = HallSerializer
