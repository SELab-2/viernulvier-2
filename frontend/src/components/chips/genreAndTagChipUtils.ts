import type { GenreAndTagChipType } from '../../types/GenreAndTagChip'

/**
 * Maps chip type to the query key used by filter URLs.
 */
export const getQueryKeyForChipType = (chipType: GenreAndTagChipType): 'g' | 't' => {
  if (chipType === 'genre') {
    return 'g'
  }

  return 't'
}
