from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """
    Base admin class used across our API.
    """

    def get_queryset(self, request):
        return super().get_queryset(request)