import type { Event } from '../types/Events'
import { formatDate } from './formatDate'
import getLocationName from './locations'

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
export function getEventDateRangeLabel(events: Event[] | undefined, language: string): string {
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

/**
 * Returns the shared location name when every event in the list takes place at
 * the same location, otherwise returns `null`.
 *
 * Two events are considered to share a location when {@link getLocationName}
 * resolves to the same non-empty string for both. Events without a hall
 * (or with a hall that resolves to an empty string) cause the function to
 * return `null` immediately.
 *
 * @param events The production's event list (may be `undefined` when not loaded).
 * @param language BCP 47 locale tag for {@link getLocationName}.
 * @returns The shared location label, or `null` when locations differ or are absent.
 */
export function getSharedLocationName(
  events: Event[] | undefined,
  language: string,
): string | null {
  if (!events || events.length === 0) {
    return null
  }

  const names = events.map((e) => getLocationName(e.hall, language))

  const first = names[0]
  if (!first) {
    return null
  }

  if (names.every((n) => n === first)) {
    return first
  }

  return null
}
