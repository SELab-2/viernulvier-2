import type { Event } from '../types/Events'

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
 * Builds a human-readable date-range label from a production's event list.
 *
 * Events are sorted by `starts_at`. When the first and last dates resolve to
 * the same formatted string the label is just that single date. Otherwise the
 * label is `"startDate – endDate"`.
 *
 * @param events The production's event list (may be `undefined` when not loaded).
 * @param language BCP 47 locale tag for {@link formatDate}.
 * @returns Formatted range string, or `''` when there are no dateable events.
 */
export function getProductionDateLabel(events: Event[] | undefined, language: string): string {
  if (!events || events.length === 0) {
    return ''
  }

  const sorted = [...events]
    .filter((e) => e.starts_at)
    .sort((a, b) => new Date(a.starts_at!).getTime() - new Date(b.starts_at!).getTime())
  if (sorted.length === 0) {
    return ''
  }

  const first = formatDate(sorted[0].starts_at, language)
  if (!first) {
    return ''
  }

  const last = formatDate(sorted[sorted.length - 1].starts_at, language)
  if (!last || first === last) {
    return first
  }

  return `${first} - ${last}`
}
