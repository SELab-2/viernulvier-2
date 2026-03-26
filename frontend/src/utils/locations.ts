import type { Hall } from '../types/Halls'
import { getTranslatedRecord } from './translations'

/**
 * Resolves a short venue label for a {@link Hall} for map/list UI.
 *
 * Order of precedence: translated **location** name → **space** name → **hall** name. Empty strings
 * at each step fall through to the next source (see {@link getTranslatedRecord}).
 *
 * @param hall The hall (may include nested `space` / `location`); `null` / `undefined` yields `''`.
 * @param language The active UI language key matching keys in translation records.
 * @returns The first non-empty translated label, or `''` if none apply.
 */
function getLocationName(hall: Hall | null | undefined, language: string): string {
  const locationTranslation = getTranslatedRecord(
    hall?.space?.location?.name,
    language,
    hall?.space?.location?.display_name,
  )
  if (locationTranslation) {
    return locationTranslation
  }

  const spaceTranslation = getTranslatedRecord(
    hall?.space?.name,
    language,
    hall?.space?.display_name,
  )
  if (spaceTranslation) {
    return spaceTranslation
  }

  const hallTranslation = getTranslatedRecord(hall?.name, language, hall?.display_name)
  if (hallTranslation) {
    return hallTranslation
  }

  return ''
}

export default getLocationName
