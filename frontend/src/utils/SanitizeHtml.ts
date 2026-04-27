import DOMPurify from 'dompurify'

function decodeHtmlEntities(html: string): string {
  const element = document.createElement('textarea')
  element.innerHTML = html
  return element.value
}

function looksLikeEscapedHtml(html: string): boolean {
  return /&lt;|&gt;|&#\d+;|&amp;/i.test(html)
}

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
  const normalizedHtml = looksLikeEscapedHtml(html) ? decodeHtmlEntities(html) : html

  return DOMPurify.sanitize(normalizedHtml, {
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
