"""Models for the Blog app.

Blogs are content pages that can be linked to productions and displayed
on the frontend as standalone pages or linked from production detail pages.
"""

from django.db import models

from apps.core.models import BaseModel
from apps.languages.models import Language
from apps.productions.models import Production


class Blog(BaseModel):
    """Core blog/content page entity.

    A blog represents a CMS-managed content page (e.g., articles, news,
    historical posts) that can be linked to one or more productions.

    Each blog has:
    - A technical ``slug`` for SEO-friendly URLs
    - An optional ``published_at`` timestamp
    - An optional ``cover_image`` for visual representation
    - A many-to-many relationship to ``Production``
    - One or more ``translations`` (localized title and body)
    """

    slug = models.SlugField(
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        help_text="URL-friendly identifier for this blog post (e.g., 'i-love-techno-2024').",
        db_comment="SEO-friendly slug for the blog post.",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Publication timestamp. If null, the post is considered a draft.",
        db_comment="Publication date and time.",
    )

    cover_image = models.ImageField(
        upload_to="blog_covers/",
        null=True,
        blank=True,
        help_text="Upload a cover image for this blog post.",
    )

    productions = models.ManyToManyField(
        Production,
        related_name="blogs",
        blank=True,
        help_text="Productions linked to this blog post.",
    )

    class Meta(BaseModel.Meta):
        db_table = "blog"
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ["-published_at", "-id"]

    def __str__(self) -> str:
        """Return a human-readable representation, preferring the base display name, then slug."""
        name = self.get_base_display_name(
            related_name="translations",
            fallback=None,
            name_field="title",
        )

        if name:
            return name

        return self.slug


class BlogTranslation(BaseModel):
    """Localized content for a Blog.

    Each blog can have at most one translation per language.
    """

    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text="Localized title of the blog post.",
        db_comment="Translated title.",
    )

    body = models.TextField(
        null=False,
        blank=False,
        help_text="Localized body content (supports HTML or Markdown).",
        db_comment="Translated body content.",
    )

    excerpt = models.TextField(
        null=True,
        blank=True,
        help_text="Optional short excerpt or summary of the post.",
        db_comment="Translated excerpt.",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="blog_translations",
        help_text="Language of this translation.",
        db_comment="FK to Language.",
    )

    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE,
        related_name="translations",
        help_text="Blog post this translation belongs to.",
        db_comment="FK to Blog.",
    )

    class Meta(BaseModel.Meta):
        db_table = "blog_translation"
        verbose_name = "Blog Translation"
        verbose_name_plural = "Blog Translations"
        ordering = ["id"]
        unique_together = [["blog", "language"]]

    def __str__(self) -> str:
        """Return a string representation of the translation."""
        return f"{self.language.code} - {self.title}"
