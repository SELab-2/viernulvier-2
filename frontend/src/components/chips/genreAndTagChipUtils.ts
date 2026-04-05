import { getTranslatedRecord } from '../../utils/translations'
import type { ChipLabels, GenreAndTagChipType } from '../../types/GenreAndTagChip'

/**
 * Maps chip type to the query key used by filter URLs.
 */
export const getQueryKeyForChipType = (chipType: GenreAndTagChipType): 'g' | 't' => {
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
  labels: ChipLabels
  language: string
}): string => {
  return getTranslatedRecord(labels, language, fallback)
}
