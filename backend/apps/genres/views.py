from apps.core.views import ApiModelViewSet
from .models import Genre, GenreTranslation, GenreUseAs
from .serializers import GenreSerializer, GenreTranslationSerializer, GenreUseAsSerializer


class GenreUseAsViewSet(ApiModelViewSet):
	"""
	API endpoint for managing GenreUseAs entries.

	Access rules:
		- Public API key -> read-only
		- Internal API key -> full CRUD
	"""

	queryset = GenreUseAs.objects.all()
	serializer_class = GenreUseAsSerializer


class GenreViewSet(ApiModelViewSet):
	"""
	API endpoint for managing genres.

	Access rules:
		- Public API key -> read-only
		- Internal API key -> full CRUD
	"""

	queryset = Genre.objects.select_related("use_as").prefetch_related("translations__language").all()
	serializer_class = GenreSerializer


class GenreTranslationViewSet(ApiModelViewSet):
	"""
	API endpoint for managing genre translations.

	Access rules:
		- Public API key -> read-only
		- Internal API key -> full CRUD
	"""

	queryset = GenreTranslation.objects.select_related("genre", "language").all()
	serializer_class = GenreTranslationSerializer
