/**
 * Formats an ISO date string for display using {@link Intl.DateTimeFormat} (long month, numeric
 * day and year).
 *
 * @param iso An ISO 8601 string, or `null` / `undefined` (returns an empty string).
 * @param locale A BCP 47 language tag (e.g. `nl`, `en-US`); should match the active UI locale.
 * @returns The formatted date, or an empty string if `iso` is missing or not parseable.
 */
export function formatDate(iso: string | null | undefined, locale: string): string {
  if (!iso) {
    return ''
  }

  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}
