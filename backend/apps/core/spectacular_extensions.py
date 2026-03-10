from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    OpenAPI extension for drf-spectacular to document Api-Key auth.
    """

    target_class = "apps.core.authentications.ApiKeyAuthentication"
    name = "ApiKey"
    match_subclasses = True

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Use `Api-Key <Key>` to authenticate.",
        }
