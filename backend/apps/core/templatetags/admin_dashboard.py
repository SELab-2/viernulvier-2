"""Template tags for rendering the custom Django admin dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django import template
from django.contrib import admin
from django.urls import NoReverseMatch, reverse

from apps.blogs.models import Blog
from apps.events.models import Event
from apps.media_files.models import MediaFile
from apps.productions.models import Production
from apps.tags.models import Tag

register = template.Library()


@dataclass(frozen=True)
class DashboardCardSpec:
    """Configuration for one dashboard card on the admin index page."""

    title: str
    description: str
    model: type


CARD_SPECS = (
    DashboardCardSpec(
        title="Productions",
        description="Core catalogue entries and metadata.",
        model=Production,
    ),
    DashboardCardSpec(
        title="Events",
        description="Scheduled showtimes and venue planning.",
        model=Event,
    ),
    DashboardCardSpec(
        title="Blogs",
        description="Published and draft editorial posts.",
        model=Blog,
    ),
    DashboardCardSpec(
        title="Tags",
        description="Taxonomy labels for content discovery.",
        model=Tag,
    ),
    DashboardCardSpec(
        title="Media Files",
        description="Uploaded files used across the platform.",
        model=MediaFile,
    ),
)


def _model_admin_url(model: type) -> str | None:
    """Return changelist URL for a registered model or ``None``."""
    opts = model._meta
    try:
        return reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
    except NoReverseMatch:
        return None


def _model_admin_add_url(model: type) -> str | None:
    """Return add URL for a registered model or ``None``."""
    opts = model._meta
    try:
        return reverse(f"admin:{opts.app_label}_{opts.model_name}_add")
    except NoReverseMatch:
        return None


@register.simple_tag(takes_context=True)
def dashboard_cards(context: dict) -> list[dict[str, str | int]]:
    """Return dashboard cards for key models visible to the current user."""
    request = context.get("request")
    if request is None:
        return []

    cards: list[dict[str, str | int]] = []
    for spec in CARD_SPECS:
        model_admin = admin.site._registry.get(spec.model)
        if model_admin is None:
            continue

        if not model_admin.has_module_permission(request):
            continue

        if not model_admin.has_view_or_change_permission(request):
            continue

        url = _model_admin_url(spec.model)
        if not url:
            continue

        add_url = _model_admin_add_url(spec.model) if model_admin.has_add_permission(request) else None

        cards.append(
            {
                "title": spec.title,
                "description": spec.description,
                "count": spec.model._default_manager.count(),
                "url": url,
                "add_url": add_url,
            }
        )

    return cards


def _build_multiselect_options(cl: Any, spec: Any) -> list[dict[str, Any]]:
    """Return renderable option data for a searchable multiselect filter.

    Counts are obtained through Django's facet queryset machinery so the
    admin's ``_facets`` toggle controls when they are calculated.
    """
    facet_counts: dict[str, Any] = {}
    if getattr(cl, "add_facets", False):
        facet_counts = spec.get_facet_queryset(cl)

    options: list[dict[str, Any]] = []
    for index, (value, label) in enumerate(spec.lookup_choices):
        options.append(
            {
                "value": value,
                "label": label,
                "selected": value in spec.selected_values,
                "count": facet_counts.get(f"{index}__c"),
            }
        )

    return options


@register.simple_tag
def multiselect_options(cl: Any, spec: Any) -> list[dict[str, Any]]:
    """Return option dictionaries for the multiselect filter template."""
    return _build_multiselect_options(cl, spec)
