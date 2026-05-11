import { PARAM_GENRES, PARAM_TAGS } from '../../shared/hooks/useSearchBarUrlState'

import type { GenreAndTagChipType } from '../../types/GenreAndTagChip'

/**
 * Maps chip types to their corresponding URL query keys.
 */
export const getQueryKeyForChipType = (chipType: GenreAndTagChipType): string => {
  if (chipType === 'genre') {
    return PARAM_GENRES
  }

  return PARAM_TAGS
}
