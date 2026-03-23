"""
Cache invalidation signals for read-heavy API endpoints.

Provides a single helper, ``connect_cache_invalidation``, that wires
post_save and post_delete signals for a given model to a handler that
clears all cache entries matching a URL prefix. This ensures that
cached list and retrieve responses are invalidated whenever the
underlying data changes.
"""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save


def connect_cache_invalidation(model, url_prefix):
    """
    Connects post_save and post_delete signals for the given model to a
    handler that clears all cache entries matching the given URL prefix.
    """
    def handler(sender, **kwargs):
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern(f"*{url_prefix}*")
        else:
            cache.clear()

    post_save.connect(handler, sender=model, weak=False)
    post_delete.connect(handler, sender=model, weak=False)
