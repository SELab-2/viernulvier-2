/**
 * Retrieves a localized string from an object keyed by language codes.
 *
 * If the requested language is not available, the function falls back to the
 * first available value in the object. When the input is `null`, `undefined`,
 * or not an object, an empty string is returned.
 *
 * @param obj An object mapping BCP 47 language tags to localized strings.
 * @param lang The preferred language code (defaults to `'nl'`).
 * @returns The localized string, a fallback value, or an empty string when unavailable.
 */
export function getLocalizedValue(
  obj: Record<string, string> | null | undefined,
  lang = 'nl',
): string {
  if (!obj || typeof obj !== 'object') {
    return ''
  }
  return obj[lang] || Object.values(obj)[0] || ''
}