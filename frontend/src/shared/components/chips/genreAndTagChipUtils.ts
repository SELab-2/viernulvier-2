import { PARAM_GENRES, PARAM_TAGS } from '../../hooks/useSearchBarUrlState'

import type { GenreAndTagChipType } from '../../../types/GenreAndTagChip'

const FILTER_SEPARATOR = '-'

/**
 * Reads a query parameter that may be encoded as repeated values or as a single
 * `-`-separated token list.
 */
export const readMultiParamValues = (
  searchParams: URLSearchParams,
  paramName: string,
): string[] => {
  const repeatedValues = searchParams.getAll(paramName)
  if (repeatedValues.length > 0) {
    return repeatedValues.flatMap((value) => parseTokenList(value))
  }

  const serialized = searchParams.get(paramName)
  return parseTokenList(serialized)
}

const parseTokenList = (value: string | null): string[] => {
  if (!value) {
    return []
  }

  return value
    .split(FILTER_SEPARATOR)
    .map((part) => part.trim())
    .filter(Boolean)
}

/**
 * Maps chip types to their corresponding URL query keys.
 */
export const getQueryKeyForChipType = (chipType: GenreAndTagChipType): string => {
  if (chipType === 'genre') {
    return PARAM_GENRES
  }

  return PARAM_TAGS
}
