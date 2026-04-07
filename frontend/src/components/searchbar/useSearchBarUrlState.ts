import { useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './types'

const DEFAULT_SEARCH_SORT_TARGET: SearchSortTarget = 'date'
const DEFAULT_SEARCH_SORT_DIRECTION: SearchSortDirection = 'desc'
const DEFAULT_SEARCH_VIEW_MODE: SearchViewMode = 'grid'

const PARAM_QUERY = 'q'
const PARAM_SORT_TARGET = 'st'
const PARAM_SORT_DIRECTION = 'sd'
const PARAM_VIEW = 'v'
const PARAM_GENRES = 'g'
const PARAM_TAGS = 't'
const FILTER_SEPARATOR = '~'

/**
 * Parses compact filter text into tokens.
 * Supports `~` as a separator for multiple values, and trims whitespace.
 * Returns an empty array for null or empty input.
 */
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
 * Converts array tokens to number IDs and removes invalid values.
 */
const parseNumericIds = (values: string[]): number[] => {
  return values.map((part) => Number(part)).filter((part) => Number.isFinite(part))
}

/**
 * Reads query params and supports both single and repeated encodings.
 */
const readMultiParamValues = (searchParams: URLSearchParams, paramName: string): string[] => {
  const repeatedValues = searchParams.getAll(paramName)
  if (repeatedValues.length > 0) {
    return repeatedValues.flatMap((value) => parseTokenList(value))
  }

  const serialized = searchParams.get(paramName)
  return parseTokenList(serialized)
}

/**
 * Encodes list values into one compact query value.
 */
const encodeTokenList = (values: Array<string | number>): string | null => {
  if (!values.length) {
    return null
  }

  return values.join(FILTER_SEPARATOR)
}

/**
 * Toggles a value in an array for URL-based multi-select state.
 */
const toggleArrayValue = <T extends string | number>(values: T[], value: T): T[] => {
  if (values.includes(value)) {
    return values.filter((item) => item !== value)
  }

  return [...values, value]
}

const parseSearchSortTarget = (value: string | null): SearchSortTarget => {
  if (value === 'n') {
    return 'name'
  }

  if (value === 'd') {
    return 'date'
  }

  return DEFAULT_SEARCH_SORT_TARGET
}

const parseSearchSortDirection = (value: string | null): SearchSortDirection => {
  if (value === 'a') {
    return 'asc'
  }

  if (value === 'd') {
    return 'desc'
  }

  return DEFAULT_SEARCH_SORT_DIRECTION
}

const parseSearchViewMode = (value: string | null): SearchViewMode => {
  if (value === 'l') {
    return 'list'
  }

  if (value === 'g') {
    return 'grid'
  }

  return DEFAULT_SEARCH_VIEW_MODE
}

const encodeSortTarget = (value: SearchSortTarget): string | null => {
  if (value === DEFAULT_SEARCH_SORT_TARGET) {
    return null
  }

  return value === 'name' ? 'n' : 'd'
}

const encodeSortDirection = (value: SearchSortDirection): string | null => {
  if (value === DEFAULT_SEARCH_SORT_DIRECTION) {
    return null
  }

  return value === 'asc' ? 'a' : 'd'
}

const encodeViewMode = (value: SearchViewMode): string | null => {
  if (value === DEFAULT_SEARCH_VIEW_MODE) {
    return null
  }

  return value === 'list' ? 'l' : 'g'
}

type UpdateSearchParamsInput = {
  q?: string
  sortTarget?: SearchSortTarget
  sortDirection?: SearchSortDirection
  view?: SearchViewMode
  genres?: number[]
  tags?: number[]
}

type UseSearchBarUrlStateOptions = {
  isMobile: boolean
}

export type SearchBarUrlState = {
  searchValue: string
  sortTarget: SearchSortTarget
  sortDirection: SearchSortDirection
  viewMode: SearchViewMode
  selectedGenreIds: number[]
  selectedSeriesTagIds: number[]
  setSearchValue: (value: string) => void
  setSortTarget: (value: SearchSortTarget) => void
  setSortDirection: (value: SearchSortDirection) => void
  setViewMode: (value: SearchViewMode) => void
  toggleGenreId: (id: number) => void
  toggleSeriesTagId: (id: number) => void
}

export const useSearchBarUrlState = ({
  isMobile,
}: UseSearchBarUrlStateOptions): SearchBarUrlState => {
  const [searchParams, setSearchParams] = useSearchParams()

  const searchValue = searchParams.get(PARAM_QUERY) ?? ''
  const sortTarget = parseSearchSortTarget(searchParams.get(PARAM_SORT_TARGET))
  const sortDirection = parseSearchSortDirection(searchParams.get(PARAM_SORT_DIRECTION))
  const parsedViewMode = parseSearchViewMode(searchParams.get(PARAM_VIEW))
  const viewMode: SearchViewMode = isMobile ? DEFAULT_SEARCH_VIEW_MODE : parsedViewMode
  const genreParamValues = [...readMultiParamValues(searchParams, PARAM_GENRES)]
  const tagParamValues = [...readMultiParamValues(searchParams, PARAM_TAGS)]
  const selectedGenreIds = parseNumericIds(genreParamValues)
  const selectedSeriesTagIds = parseNumericIds(tagParamValues)

  const updateSearchParams = useCallback(
    ({
      q,
      sortTarget: nextSortTarget,
      sortDirection: nextSortDirection,
      view,
      genres,
      tags,
    }: UpdateSearchParamsInput) => {
      setSearchParams(
        (currentParams) => {
          const nextParams = new URLSearchParams(currentParams)

          if (q !== undefined) {
            if (q.trim()) {
              nextParams.set(PARAM_QUERY, q)
            } else {
              nextParams.delete(PARAM_QUERY)
            }
          }

          if (nextSortTarget !== undefined) {
            const encodedSortTarget = encodeSortTarget(nextSortTarget)
            if (encodedSortTarget) {
              nextParams.set(PARAM_SORT_TARGET, encodedSortTarget)
            } else {
              nextParams.delete(PARAM_SORT_TARGET)
            }
          }

          if (nextSortDirection !== undefined) {
            const encodedSortDirection = encodeSortDirection(nextSortDirection)
            if (encodedSortDirection) {
              nextParams.set(PARAM_SORT_DIRECTION, encodedSortDirection)
            } else {
              nextParams.delete(PARAM_SORT_DIRECTION)
            }
          }

          if (view !== undefined) {
            const effectiveViewMode: SearchViewMode = isMobile ? DEFAULT_SEARCH_VIEW_MODE : view
            const encodedViewMode = encodeViewMode(effectiveViewMode)
            if (encodedViewMode) {
              nextParams.set(PARAM_VIEW, encodedViewMode)
            } else {
              nextParams.delete(PARAM_VIEW)
            }
          }

          if (genres !== undefined) {
            const encodedGenres = encodeTokenList(genres)
            if (encodedGenres) {
              nextParams.set(PARAM_GENRES, encodedGenres)
            } else {
              nextParams.delete(PARAM_GENRES)
            }
          }

          if (tags !== undefined) {
            const encodedTags = encodeTokenList(tags)
            if (encodedTags) {
              nextParams.set(PARAM_TAGS, encodedTags)
            } else {
              nextParams.delete(PARAM_TAGS)
            }
          }

          return nextParams
        },
        { replace: true },
      )
    },
    [isMobile, setSearchParams],
  )

  useEffect(() => {
    if (isMobile && searchParams.get(PARAM_VIEW) !== null) {
      updateSearchParams({ view: DEFAULT_SEARCH_VIEW_MODE })
    }
  }, [isMobile, searchParams, updateSearchParams])

  return {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    selectedGenreIds,
    selectedSeriesTagIds,
    setSearchValue: (value: string) => updateSearchParams({ q: value }),
    setSortTarget: (value: SearchSortTarget) => updateSearchParams({ sortTarget: value }),
    setSortDirection: (value: SearchSortDirection) => updateSearchParams({ sortDirection: value }),
    setViewMode: (value: SearchViewMode) => updateSearchParams({ view: value }),
    toggleGenreId: (id: number) =>
      updateSearchParams({ genres: toggleArrayValue(selectedGenreIds, id) }),
    toggleSeriesTagId: (id: number) =>
      updateSearchParams({ tags: toggleArrayValue(selectedSeriesTagIds, id) }),
  }
}
