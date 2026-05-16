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

/**
 * Formats an ISO date string for blog publication display using {@link Intl.DateTimeFormat}
 * (2-digit day, short month, numeric year).
 *
 * @param value An ISO 8601 string, or `null` (returns `null`).
 * @param language A BCP 47 language tag (e.g. `nl`, `en-US`); should match the active UI locale.
 * @returns The formatted date string, or `null` if `value` is missing or not parseable.
 */
export const formatBlogPublishedDate = (value: string | null, language: string): string | null => {
  if (!value) {
    return null
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return null
  }

  return new Intl.DateTimeFormat(language, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

/**
 * Formats an ISO time string for display (hour + minute).
 *
 * @param iso An ISO 8601 string, or `null` / `undefined`.
 * @param locale A BCP 47 language tag.
 * @returns The formatted time or empty string for invalid values.
 */
export function formatTime(iso: string | null | undefined, locale: string): string {
  if (!iso) {
    return ''
  }

  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

/**
 * Formats an ISO date-time string with date and time for display.
 *
 * @param iso An ISO 8601 string, or `null` / `undefined` (returns empty string).
 * @param locale A BCP 47 language tag (e.g. `nl`, `en-GB`).
 * @returns The formatted date-time or an empty string for invalid values.
 */
export function formatDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) {
    return ''
  }

  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

/**
 * Builds a human-readable date label from a production's event list.
 *
 * If only one endpoint is available, that date is shown. When both dates are
 * available and resolve to the same formatted string, the label is just that
 * single date. Otherwise the label is `"startDate - endDate"`.
 *
 * @param firstEventStart The production's first event start date.
 * @param lastEventEnd The production's last event end date.
 * @param language BCP 47 locale tag for {@link formatDate}.
 * @returns Formatted date string, range string, or `''` when both values are missing.
 */
export function getProductionDateLabel(
  firstEventStart: string | null,
  lastEventEnd: string | null,
  language: string,
): string {
  const first = formatDate(firstEventStart, language)
  const last = formatDate(lastEventEnd, language)

  if (!last) {
    return first
  }

  if (!first) {
    return last
  }

  if (first === last) {
    return first
  }

  return `${first} - ${last}`
}
