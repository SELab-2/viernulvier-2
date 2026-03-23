"""
Cache invalidation signals for read-heavy API endpoints.

Provides a single helper, ``connect_cache_invalidation``, that wires
post_save and post_delete signals for a given model to a handler that
clears cached responses whenever the underlying data changes.

When using django-redis, only keys matching the url_prefix are deleted.
Falls back to cache.clear() for other backends (e.g. LocMemCache in tests).
"""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save


def connect_cache_invalidation(model, url_prefix):
    """
    Connect post_save and post_delete signals for the given model to a
    handler that invalidates cached responses for the given url_prefix.

    Uses delete_pattern (django-redis) when available for targeted
    invalidation. Falls back to cache.clear() for other backends.

    Uses stable dispatch_uids so repeated calls do not register duplicate
    receivers during tests or app startup.
    """
    def handler(sender, **kwargs):
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern(f"*{url_prefix}*")
        else:
            cache.clear()

    model_label = model._meta.label_lower
    uid_base = f"cache_invalidation:{model_label}:{url_prefix}"

    post_save.connect(
        handler,
        sender=model,
        weak=False,
        dispatch_uid=f"{uid_base}:post_save",
    )
    post_delete.connect(
        handler,
        sender=model,
        weak=False,
        dispatch_uid=f"{uid_base}:post_delete",
    )
