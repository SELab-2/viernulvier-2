import type { Event } from '../types/Events'

/**
 * Returns a hall display preview for the desired language.
 *
 * - First try event.hall.name[locale]
 * - If not available, fall back to event.hall_display
 */
export function getHallDisplayName(event: Event, lang: string): string | null {
  const locale = lang.split('-')[0] || 'nl'
  const hallName = event.hall?.name

  if (hallName && hallName[locale]) {
    return hallName[locale]
  }

  return event.hall_display || null
}
