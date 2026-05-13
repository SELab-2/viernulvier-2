"""drf-spectacular extensions for documenting core authentication schemes."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    """OpenAPI extension for drf-spectacular to document X-API-Key auth."""

    target_class = "apps.core.authentications.ApiKeyAuthentication"
    name = "ApiKey"
    match_subclasses = True

    def get_security_definition(self, _auto_schema: any) -> dict:
        """Return the OpenAPI security scheme definition for API key authentication."""
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Use the `X-API-Key` header to authenticate.",
        }
