import { Hall } from '../types/Halls'
import { getTranslatedRecord } from './translations'

function getLocationName(hall: Hall | null | undefined, language: string): string {
  const locationTranslation = getTranslatedRecord(hall?.space?.location?.name, language)
  if (locationTranslation) {
    return locationTranslation
  }

  const spaceTranslation = getTranslatedRecord(hall?.space?.name, language)
  if (spaceTranslation) {
    return spaceTranslation
  }

  const hallTranslation = getTranslatedRecord(hall?.name, language)
  if (hallTranslation) {
    return hallTranslation
  }

  return ''
}

export default getLocationName
