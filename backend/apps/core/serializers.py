"""
Shared serializer utilities for the core app.

``TranslatableSerializerMixin`` is the single mechanism used across the
project for serialising localised content. Every serializer that exposes
translated fields should inherit from this mixin and call
:meth:`get_translated_field` inside its ``SerializerMethodField`` getters.

Translation format
------------------
Translated fields are returned as a dictionary mapping language codes to
their localised values::

    {
        "title": {
            "nl": "De Laatste Avond",
            "en": "The Last Evening",
            "fr": "Le Dernier Soir"
        }
    }

Language codes with an empty or falsy value are omitted from the dictionary
so consumers always receive only the languages that have actual content.

Performance
-----------
The mixin reads from the prefetched ``translations`` relation. For this to
be query-free, viewsets must include the relevant ``Prefetch`` in their
queryset. See the individual app viewsets for examples.
"""

from django.conf import settings

class TranslatableSerializerMixin:
    """
    Mixin that adds :meth:`get_translated_field` to any DRF serializer.

    Converts a model's translation rows into a ``{language_code: value}``
    dictionary. Designed to be used alongside Django's ``prefetch_related``
    so that accessing translations never triggers additional database queries.

    Usage
    -----
    Inherit from both this mixin and ``serializers.ModelSerializer``, then
    call :meth:`get_translated_field` inside ``SerializerMethodField``
    getters::

        class MySerializer(TranslatableSerializerMixin, serializers.ModelSerializer):
            title = serializers.SerializerMethodField()

            def get_title(self, obj):
                return self.get_translated_field(obj, "title")

    Note that ``TranslatableSerializerMixin`` should appear **before**
    ``serializers.ModelSerializer`` in the inheritance list so that Python's
    MRO resolves its methods first.
    """

    def get_translated_field(
        self,
        obj,
        field_name: str,
        related_name: str = "translations",
    ) -> dict:
        """
        Build a ``{language_code: value}`` dictionary for a translated field.

        Reads translation rows from ``obj.<related_name>.all()`` — which is
        expected to be a prefetched queryset — and returns a dictionary of
        all languages that have a non-empty value for ``field_name``.

        Parameters
        ----------
        obj:
            The model instance being serialised. Must have a ``related_name``
            reverse relation whose rows each have a ``language`` FK with a
            ``code`` attribute, and a field named ``field_name``.
        field_name:
            The name of the translated field to extract
            (e.g. ``"title"``, ``"description"``).
        related_name:
            The reverse relation name on ``obj`` that holds the translation
            rows. Defaults to ``"translations"``, which matches the
            ``related_name`` used on translation FK fields throughout the
            project.

        Returns
        -------
        dict
            A ``{language_code: value}`` mapping containing only languages
            with a truthy value for ``field_name``. Returns an empty dict
            when no translations exist or none have content for this field.

        Examples
        --------
        >>> self.get_translated_field(production, "title")
        {"nl": "De Laatste Avond", "en": "The Last Evening"}

        >>> self.get_translated_field(production, "title")  # no translations
        {}
        """
        translations = getattr(obj, related_name).all()

        return {
            t.language.code: getattr(t, field_name)
            for t in translations
            if getattr(t, field_name)
        }
    
    def get_base_language_code(self) -> str:
        """
        Return the project's primary language code.

        The base language is derived from ``settings.LANGUAGE_CODE``.
        If the setting includes a regional variant (e.g. ``"en-us"``),
        only the primary ISO 639-1 language subtag (``"en"``) is used.

        This ensures consistent behaviour across:

        - Base-language display fields in API responses
        - Admin dropdown labels
        - Any serializer that needs a single canonical language value

        Returns
        -------
        str
            The primary language code (e.g. ``"en"``, ``"nl"``, ``"fr"``).

        Examples
        --------
        >>> settings.LANGUAGE_CODE = "en-us"
        >>> self.get_base_language_code()
        "en"

        >>> settings.LANGUAGE_CODE = "nl"
        >>> self.get_base_language_code()
        "nl"
        """
        return (getattr(settings, "LANGUAGE_CODE", "en") or "en").split("-")[0].lower()

    def get_base_translated_value(
        self,
        obj,
        field_name: str,
        related_name: str = "translations",
        fallback=None,
    ):
        """
        Return a single translated value in the project's base language.

        This method is designed for API "display fields" (e.g. ``display_name``)
        where a single human-readable label is required rather than a full
        ``{language_code: value}`` mapping.

        Resolution strategy
        -------------------
        1. Prefer the translation whose ``language.code`` matches the
           project's base language (see :meth:`get_base_language_code`).
        2. If no base-language translation exists, fall back to the first
           non-empty translation value available.
        3. If no translations contain a truthy value for ``field_name``,
           return ``fallback``.

        Performance considerations
        --------------------------
        This method reads from ``obj.<related_name>.all()`` and therefore
        assumes the relation has been prefetched in the queryset. When used
        correctly alongside ``prefetch_related``, no additional database
        queries are triggered.

        Parameters
        ----------
        obj:
            The model instance being serialised. Must expose a reverse
            relation named ``related_name`` whose rows contain:

            - a ``language`` FK with a ``code`` attribute
            - a field named ``field_name``

        field_name:
            The translated field to extract (e.g. ``"title"``,
            ``"description"``, ``"name"``).

        related_name:
            The reverse relation name that contains translation rows.
            Defaults to ``"translations"``, which matches the convention
            used across the project.

        fallback:
            Value returned when no suitable translation is found.
            Typically ``None`` or a technical identifier (e.g. ``obj.id``).

        Returns
        -------
        Any
            The translated value in the base language, or a fallback.

        Examples
        --------
        >>> self.get_base_translated_value(production, "title")
        "The Last Evening"

        >>> self.get_base_translated_value(price_rank, "description")
        "Student"

        >>> self.get_base_translated_value(obj, "title", fallback="Untitled")
        "Untitled"
        """
        translations = getattr(obj, related_name).all()
        base_code = self.get_base_language_code()

        first_available = None

        for t in translations:
            value = getattr(t, field_name, None)
            if not value:
                continue
            
            # If this translation matches the base language, return it immediately
            if t.language.code == base_code:
                return value
            
            # Otherwise, keep track of the first available translation as a fallback
            if first_available is None:
                first_available = value

        return first_available or fallback