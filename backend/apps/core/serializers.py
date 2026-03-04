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

    def get_translated_field(self, obj, field_name):
        """
        Converts translations into a dictionary mapping language codes to values.
        Example: {"nl": "Titel", "en": "Title"}
        """
        translations = obj.translations.all()

        return {
            t.language.code: getattr(t, field_name)
            for t in translations
            if getattr(t, field_name)
        }
