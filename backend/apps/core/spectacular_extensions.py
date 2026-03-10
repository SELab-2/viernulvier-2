from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    OpenAPI extension for drf-spectacular to document X-API-Key auth.
    """

    target_class = "apps.core.authentications.ApiKeyAuthentication"
    name = "ApiKey"
    match_subclasses = True

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Use the `X-API-Key` header to authenticate.",
        }
