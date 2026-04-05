import { getTranslatedRecord } from '../../utils/translations'

/**
 * Maps chip type to the query key used by filter URLs.
 */
export const getQueryKeyForChipType = (chipType: 'genre' | 'seriesTag'): 'g' | 't' => {
  if (chipType === 'genre') {
    return 'g'
  }

  return 't'
}

/**
 * Resolves a translated string for a chip label given a fallback,
 * record of localized labels, and the active language.
 */
export const resolveChipLabel = ({
  fallback,
  labels,
  language,
}: {
  fallback: string
  labels?: Record<string, string>
  language: string
}): string => {
  return getTranslatedRecord(labels, language, fallback)
}
