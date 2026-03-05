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

        return {t.language.code: getattr(t, field_name) for t in translations if getattr(t, field_name)}
