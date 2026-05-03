import DOMPurify, { type Config } from 'dompurify'

/**
 * A composable rule that mutates / extends a DOMPurify config.
 *
 * Rules are applied in order inside {@link sanitizeHtml}. The default rules are
 * always executed first. Any extra rules can only make the sanitizer stricter.
 */
export type SanitizeHtmlRule = (config: Config) => Config

/**
 * Safely converts a DOMPurify config field that can be either:
 *   - string[]
 *   - function
 *   - undefined
 *
 * into a string[] so we can safely spread and extend it without errors.
 */
function asArray(value: string[] | ((...args: string[]) => boolean) | undefined): string[] {
  return Array.isArray(value) ? value : []
}

/**
 * The default rules used everywhere in the frontend when {@link sanitizeHtml}
 *
 * These rules represent the current, production-safe baseline behaviour:
 * - Use DOMPurify's HTML profile
 * - Forbid `<script>` and `<br>` tags
 * - Allow `<img>` with safe attributes
 * - Explicitly forbid all JS event handler attributes (`on*`)
 */
const defaultRules: SanitizeHtmlRule[] = [
  (config) => ({
    ...config,
    USE_PROFILES: { html: true },
  }),

  (config) => ({
    ...config,
    FORBID_TAGS: [...asArray(config.FORBID_TAGS), 'br', 'script'],
  }),

  (config) => ({
    ...config,
    ADD_TAGS: [...asArray(config.ADD_TAGS), 'img'],
    ADD_ATTR: [...asArray(config.ADD_ATTR), 'alt', 'height', 'src', 'style', 'title', 'width'],
  }),

  (config) => ({
    ...config,
    FORBID_ATTR: [
      ...asArray(config.FORBID_ATTR),
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
  }),
]

/**
 * Rule that explicitly forbids rendering `<img>` tags.
 *
 * Useful in contexts such as previews, excerpts or cards where images
 * would break layout or be visually undesirable.
 */
export const forbidImagesRule: SanitizeHtmlRule = (config) => ({
  ...config,
  FORBID_TAGS: [...asArray(config.FORBID_TAGS), 'img'],
})

/*
 * Rule that forces all `<img>` tags to have no styling or dimensions, so they render as simple elements.
 * This is used to fix a bug where images get rendered next to the text, disturbing the layout.
 */
export const sanitizeImagesStrictRule: SanitizeHtmlRule = (config) => ({
  ...config,

  FORBID_ATTR: [...asArray(config.FORBID_ATTR), 'style', 'width', 'height', 'align'],
})

/**
 * Rule that explicitly forbids embedded content such as `<iframe>`.
 *
 * Useful for excerpts, previews and cards where layout must remain predictable.
 */
export const forbidEmbedsRule: SanitizeHtmlRule = (config) => ({
  ...config,
  FORBID_TAGS: [...asArray(config.FORBID_TAGS), 'iframe'],
})

/**
 * Converts backend HTML snippets into plain text for compact UI surfaces.
 *
 * This is intended for cards, list rows and other summary layouts where the
 * content should stay readable but never render markup.
 */
export function htmlToPlainText(html: string): string {
  const normalizedHtml = looksLikeEscapedHtml(html) ? decodeHtmlEntities(html) : html
  const blockSeparatedHtml = normalizedHtml.replace(
    /<\/?(p|div|h[1-6]|li|ul|ol|section|article|header|footer|blockquote|tr|td|th|table|br)[^>]*>/gi,
    ' ',
  )

  const element = document.createElement('div')
  element.innerHTML = blockSeparatedHtml

  return (element.textContent ?? element.innerText ?? '').replace(/\s+/g, ' ').trim()
}

function decodeHtmlEntities(html: string): string {
  const element = document.createElement('textarea')
  element.innerHTML = html
  return element.value
}

function looksLikeEscapedHtml(html: string): boolean {
  return /&lt;|&gt;|&#\d+;|&amp;/i.test(html)
}

/**
 * Sanitizes HTML received from the backend before rendering it with
 * `dangerouslySetInnerHTML`.
 *
 * This function acts as a small "policy engine" on top of DOMPurify:
 *
 * 1. A fixed set of **default rules** is always applied (current production behaviour).
 * 2. Optional **extra rules** can be provided to further restrict or extend behaviour
 *    for specific use-cases (e.g. forbid images, allow embeds, forbid links, etc.).
 *
 * Existing calls such as `sanitizeHtml(html)` keep working exactly as before.
 * Additional restrictions can be layered in without modifying existing code.
 *
 * @param html Raw HTML string from the API (may contain escaped entities).
 * @param extraRules Optional additional rules applied after the default rules.
 * @returns Cleaned HTML string safe to inject into the React DOM.
 */
export function sanitizeHtml(html: string, extraRules: SanitizeHtmlRule[] = []): string {
  const normalizedHtml = looksLikeEscapedHtml(html) ? decodeHtmlEntities(html) : html

  let config: Config = {}

  // Apply default production rules
  for (const rule of defaultRules) {
    config = rule(config)
  }

  // Apply optional extra rules for this specific usage
  for (const rule of extraRules) {
    config = rule(config)
  }

  return DOMPurify.sanitize(normalizedHtml, config)
}
