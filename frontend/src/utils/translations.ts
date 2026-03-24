/**
 * Reads a per-language string from an API “record” object (e.g. `{ nl: '…', en: '…' }`).
 *
 * If `record[language]` is missing or empty, returns `fallback` (default `''`). Treats `null`,
 * `undefined`, and `{}` as “no record” and returns `fallback` in those cases.
 *
 * @param record A map of locale code to string, or empty / missing.
 * @param language The key to read (must match API keys, e.g. `nl`, `en`).
 * @param fallback Display string when the record has no usable value for `language` (e.g. API `display_title`).
 * @returns The resolved string for the current language, or `fallback` / `''`.
 */
export function getTranslatedRecord(
  record: Record<string, string> | null | undefined,
  language: string,
  fallback: string | null = null,
): string {
  if (fallback === null) {
    fallback = ''
  }

  if (!record || Object.keys(record).length === 0) {
    return fallback
  }

  const translation = record[language]
  if (translation) {
    return translation
  }

  return fallback
}
