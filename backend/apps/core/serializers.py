class TranslatableSerializerMixin:
    """
    Adds helper to serialize translated fields as:
    {
        "field_name": {
            "nl": "...",
            "en": "..."
        }
    }
    """

    def get_translated_field(self, obj, field_name, related_name="translations"):
        """
        Converts translations into a dictionary mapping language codes to values.
        Example: {"nl": "Titel", "en": "Title"}

        `related_name` lets you point to a non-default reverse relation.
        Defaults to "translations" to keep compatibility with existing models/tests.
        """
        translations = getattr(obj, related_name).all()

        return {
            t.language.code: getattr(t, field_name)
            for t in translations
            if getattr(t, field_name)
        }