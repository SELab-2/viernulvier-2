import DOMPurify from 'dompurify'

/**
 * Sanitize HTML content from the backend before rendering with dangerouslySetInnerHTML.
 *
 * - Uses DOMPurify html profile as base.
 * - Explicitly forbids `<script>` and `<br>` tags and JS event handler attributes (`on*`) for defense-in-depth.
 *
 * @param html Raw HTML string from production teaser/description.
 * @returns Cleaned HTML safe for insertion into React DOM.
 */
function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['br', 'script'],
    ADD_TAGS: ['img'],
    ADD_ATTR: ['alt', 'height', 'src', 'style', 'title', 'width'],
    FORBID_ATTR: [
      'onblur',
      'onclick',
      'onerror',
      'onfocus',
      'onkeydown',
      'onkeypress',
      'onkeyup',
      'onmouseleave',
      'onmouseenter',
      'onmouseover',
      'onload',
    ].sort(),
  })
}

export default sanitizeHtml
