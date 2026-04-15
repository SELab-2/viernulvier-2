import { useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'

import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './types'
import type { AttendanceMode, PerformerType } from '../../types/Productions'

// Default values for search parameters when they are not present in the URL
const DEFAULT_SEARCH_SORT_TARGET: SearchSortTarget = 'date'
const DEFAULT_SEARCH_SORT_DIRECTION: SearchSortDirection = 'desc'
const DEFAULT_SEARCH_VIEW_MODE: SearchViewMode = 'grid'
const DEFAULT_PAGE = 1

// Custom hook to manage the search bar state synchronized with URL query parameters.
const PARAM_QUERY = 'q'
const PARAM_SORT_TARGET = 'st'
const PARAM_SORT_DIRECTION = 'sd'
const PARAM_VIEW = 'v'
const PARAM_PAGE = 'p'
const PARAM_ATTENDANCE_MODE = 'am'
const PARAM_PERFORMER_TYPE = 'pt'
const PARAM_FIRST_EVENT_START_AFTER = 'fa'
const PARAM_FIRST_EVENT_START_BEFORE = 'fb'
export const PARAM_GENRES = 'g'
export const PARAM_TAGS = 't'
const FILTER_SEPARATOR = '-'
const DATE_INPUT_PATTERN = /^\d{4}-\d{2}-\d{2}$/

// Reads query parameters and supports both single value and repeated encodings.
const readMultiParamValues = (searchParams: URLSearchParams, paramName: string): string[] => {
  const repeatedValues = searchParams.getAll(paramName)
  if (repeatedValues.length > 0) {
    return repeatedValues.flatMap((value) => parseTokenList(value))
  }

  const serialized = searchParams.get(paramName)
  return parseTokenList(serialized)
}

// Toggles a value in an array for URL-based multi-select state.
const toggleArrayValue = <T extends string | number>(values: T[], value: T): T[] => {
  if (values.includes(value)) {
    return values.filter((item) => item !== value)
  }

  return [...values, value]
}

const normalizeDateInput = (value: string | null): string => {
  const normalized = value?.trim() ?? ''
  return DATE_INPUT_PATTERN.test(normalized) ? normalized : ''
}

const parseAttendanceModes = (values: string[]): AttendanceMode[] => {
  return values.filter(
    (value): value is AttendanceMode => value === 'offline' || value === 'online',
  )
}

const parsePerformerTypes = (values: string[]): PerformerType[] => {
  return values.filter((value): value is PerformerType => value === 'group' || value === 'solo')
}

// Parses the search sort target from the URL query parameter
const parseSearchSortTarget = (value: string | null): SearchSortTarget => {
  if (value === 'n') {
    return 'name'
  }

  if (value === 'd') {
    return 'date'
  }

  return DEFAULT_SEARCH_SORT_TARGET
}

// Parses the search sort direction from the URL query parameter
const parseSearchSortDirection = (value: string | null): SearchSortDirection => {
  if (value === 'a') {
    return 'asc'
  }

  if (value === 'd') {
    return 'desc'
  }

  return DEFAULT_SEARCH_SORT_DIRECTION
}

// Parses the search view mode from the URL query parameter
const parseSearchViewMode = (value: string | null): SearchViewMode => {
  if (value === 'l') {
    return 'list'
  }

  if (value === 'g') {
    return 'grid'
  }

  return DEFAULT_SEARCH_VIEW_MODE
}

// Parses the page number from the URL query parameter, ensuring it is a valid positive integer
const parsePage = (value: string | null): number => {
  if (!value) {
    return DEFAULT_PAGE
  }

  const parsed = Number.parseInt(value, 10)
  if (!Number.isFinite(parsed) || parsed < 1) {
    return DEFAULT_PAGE
  }

  return parsed
}

// Parses a string of tokens separated by FILTER_SEPARATOR into an array of trimmed, non-empty strings.
const parseTokenList = (value: string | null): string[] => {
  if (!value) {
    return []
  }

  return value
    .split(FILTER_SEPARATOR)
    .map((part) => part.trim())
    .filter(Boolean)
}

// Converts array tokens to integer IDs and removes invalid values.
const parseNumericIds = (values: string[]): number[] => {
  return values.map((part) => Number(part)).filter((part) => Number.isInteger(part))
}

const encodeOptionalString = (value: string): string | null => {
  const normalized = value.trim()
  return normalized || null
}

// Encode search sort target for URL query parameter, omit if default
const encodeSortTarget = (value: SearchSortTarget): string | null => {
  if (value === DEFAULT_SEARCH_SORT_TARGET) {
    return null
  }

  return value === 'name' ? 'n' : 'd'
}

// Encode search sort direction for URL query parameter, omit if default
const encodeSortDirection = (value: SearchSortDirection): string | null => {
  if (value === DEFAULT_SEARCH_SORT_DIRECTION) {
    return null
  }

  return value === 'asc' ? 'a' : 'd'
}

// Encode search view mode for URL query parameter, omit if default
const encodeViewMode = (value: SearchViewMode): string | null => {
  if (value === DEFAULT_SEARCH_VIEW_MODE) {
    return null
  }

  return value === 'list' ? 'l' : 'g'
}

// Encode page number for URL query parameter, omit if default (1) or invalid
const encodePage = (value: number): string | null => {
  if (!Number.isFinite(value)) {
    return null
  }

  const normalized = Math.floor(value)
  if (normalized <= DEFAULT_PAGE) {
    return null
  }

  return String(normalized)
}

// Encodes list values into one compact query value.
const encodeTokenList = (values: Array<string | number>): string | null => {
  if (!values.length) {
    return null
  }

  return values.join(FILTER_SEPARATOR)
}

type UpdateSearchParamsInput = {
  q?: string
  sortTarget?: SearchSortTarget
  sortDirection?: SearchSortDirection
  view?: SearchViewMode
  page?: number
  attendanceModes?: AttendanceMode[]
  performerTypes?: PerformerType[]
  genres?: number[]
  tags?: number[]
  firstEventStartAfter?: string
  firstEventStartBefore?: string
}

type UseSearchBarUrlStateOptions = {
  isMobile: boolean
}

export type SearchBarUrlState = {
  searchValue: string
  sortTarget: SearchSortTarget
  sortDirection: SearchSortDirection
  viewMode: SearchViewMode
  page: number
  attendanceModes: AttendanceMode[]
  performerTypes: PerformerType[]
  firstEventStartAfter: string
  firstEventStartBefore: string
  selectedGenreIds: number[]
  selectedTagIds: number[]
  selectedSeriesTagIds: number[]
  setSearchValue: (value: string) => void
  setSortTarget: (value: SearchSortTarget) => void
  setSortDirection: (value: SearchSortDirection) => void
  setViewMode: (value: SearchViewMode) => void
  setPage: (value: number) => void
  setAttendanceModes: (values: AttendanceMode[]) => void
  setPerformerTypes: (values: PerformerType[]) => void
  setFirstEventStartAfter: (value: string) => void
  setFirstEventStartBefore: (value: string) => void
  setSelectedGenreIds: (ids: number[]) => void
  setSelectedTagIds: (ids: number[]) => void
  toggleAttendanceMode: (value: AttendanceMode) => void
  togglePerformerType: (value: PerformerType) => void
  toggleGenreId: (id: number) => void
  toggleTagId: (id: number) => void
  toggleSeriesTagId: (id: number) => void
  clearFilters: () => void
}

// Custom hook to manage the search bar state synchronized with URL query parameters.
// Provides the current search value, sort target, sort direction, view mode, and page number
// along with setter functions that update the URL query parameters accordingly.
export const useSearchBarUrlState = ({
  isMobile,
}: UseSearchBarUrlStateOptions): SearchBarUrlState => {
  const [searchParams, setSearchParams] = useSearchParams()

  const searchValue = searchParams.get(PARAM_QUERY) ?? ''
  const sortTarget = parseSearchSortTarget(searchParams.get(PARAM_SORT_TARGET))
  const sortDirection = parseSearchSortDirection(searchParams.get(PARAM_SORT_DIRECTION))
  const parsedViewMode = parseSearchViewMode(searchParams.get(PARAM_VIEW))
  const page = parsePage(searchParams.get(PARAM_PAGE))
  const attendanceModes = parseAttendanceModes(
    readMultiParamValues(searchParams, PARAM_ATTENDANCE_MODE),
  )
  const performerTypes = parsePerformerTypes(
    readMultiParamValues(searchParams, PARAM_PERFORMER_TYPE),
  )
  const firstEventStartAfter = normalizeDateInput(searchParams.get(PARAM_FIRST_EVENT_START_AFTER))
  const firstEventStartBefore = normalizeDateInput(searchParams.get(PARAM_FIRST_EVENT_START_BEFORE))
  const viewMode: SearchViewMode = isMobile ? DEFAULT_SEARCH_VIEW_MODE : parsedViewMode
  const genreParamValues = [...readMultiParamValues(searchParams, PARAM_GENRES)]
  const tagParamValues = [...readMultiParamValues(searchParams, PARAM_TAGS)]
  const selectedGenreIds = parseNumericIds(genreParamValues)
  const selectedTagIds = parseNumericIds(tagParamValues)

  const updateSearchParams = useCallback(
    ({
      q,
      sortTarget: nextSortTarget,
      sortDirection: nextSortDirection,
      view,
      page: nextPage,
      attendanceModes: nextAttendanceModes,
      performerTypes: nextPerformerTypes,
      genres,
      tags,
      firstEventStartAfter: nextFirstEventStartAfter,
      firstEventStartBefore: nextFirstEventStartBefore,
    }: UpdateSearchParamsInput) => {
      setSearchParams(
        (currentParams) => {
          const nextParams = new URLSearchParams(currentParams)

          if (q !== undefined) {
            const normalizedQuery = q.trim()
            if (normalizedQuery) {
              nextParams.set(PARAM_QUERY, normalizedQuery)
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

          if (nextPage !== undefined) {
            const encodedPage = encodePage(nextPage)
            if (encodedPage) {
              nextParams.set(PARAM_PAGE, encodedPage)
            } else {
              nextParams.delete(PARAM_PAGE)
            }
          }

          if (nextAttendanceModes !== undefined) {
            const encodedAttendanceModes = encodeTokenList(nextAttendanceModes)
            if (encodedAttendanceModes) {
              nextParams.set(PARAM_ATTENDANCE_MODE, encodedAttendanceModes)
            } else {
              nextParams.delete(PARAM_ATTENDANCE_MODE)
            }
          }

          if (nextPerformerTypes !== undefined) {
            const encodedPerformerTypes = encodeTokenList(nextPerformerTypes)
            if (encodedPerformerTypes) {
              nextParams.set(PARAM_PERFORMER_TYPE, encodedPerformerTypes)
            } else {
              nextParams.delete(PARAM_PERFORMER_TYPE)
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

          if (nextFirstEventStartAfter !== undefined) {
            const encodedStartAfter = encodeOptionalString(
              normalizeDateInput(nextFirstEventStartAfter),
            )
            if (encodedStartAfter) {
              nextParams.set(PARAM_FIRST_EVENT_START_AFTER, encodedStartAfter)
            } else {
              nextParams.delete(PARAM_FIRST_EVENT_START_AFTER)
            }
          }

          if (nextFirstEventStartBefore !== undefined) {
            const encodedStartBefore = encodeOptionalString(
              normalizeDateInput(nextFirstEventStartBefore),
            )
            if (encodedStartBefore) {
              nextParams.set(PARAM_FIRST_EVENT_START_BEFORE, encodedStartBefore)
            } else {
              nextParams.delete(PARAM_FIRST_EVENT_START_BEFORE)
            }
          }

          return nextParams
        },
        { replace: true },
      )
    },
    [isMobile, setSearchParams],
  )

  // Ensure view mode is always 'grid' on mobile, clean URL if necessary
  useEffect(() => {
    if (isMobile && searchParams.get(PARAM_VIEW) !== null) {
      updateSearchParams({ view: DEFAULT_SEARCH_VIEW_MODE })
    }
  }, [isMobile, searchParams, updateSearchParams])

  useEffect(() => {
    if (searchParams.get('eid') === null) {
      return
    }

    setSearchParams(
      (currentParams) => {
        const nextParams = new URLSearchParams(currentParams)
        nextParams.delete('eid')
        return nextParams
      },
      { replace: true },
    )
  }, [searchParams, setSearchParams])

  return {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    page,
    attendanceModes,
    performerTypes,
    firstEventStartAfter,
    firstEventStartBefore,
    selectedGenreIds,
    selectedTagIds,
    selectedSeriesTagIds: selectedTagIds,
    // Any search/sort change can affect result ordering, so we reset to page 1.
    // View mode changes do not affect ordering, so we do not reset the page in that case.
    setSearchValue: (value: string) => updateSearchParams({ q: value.trim(), page: DEFAULT_PAGE }),
    setSortTarget: (value: SearchSortTarget) =>
      updateSearchParams({ sortTarget: value, page: DEFAULT_PAGE }),
    setSortDirection: (value: SearchSortDirection) =>
      updateSearchParams({ sortDirection: value, page: DEFAULT_PAGE }),
    setViewMode: (value: SearchViewMode) => updateSearchParams({ view: value }),
    setPage: (value: number) => updateSearchParams({ page: value }),
    setAttendanceModes: (values: AttendanceMode[]) =>
      updateSearchParams({ attendanceModes: values, page: DEFAULT_PAGE }),
    setPerformerTypes: (values: PerformerType[]) =>
      updateSearchParams({ performerTypes: values, page: DEFAULT_PAGE }),
    setFirstEventStartAfter: (value: string) =>
      updateSearchParams({ firstEventStartAfter: value, page: DEFAULT_PAGE }),
    setFirstEventStartBefore: (value: string) =>
      updateSearchParams({ firstEventStartBefore: value, page: DEFAULT_PAGE }),
    setSelectedGenreIds: (ids: number[]) => updateSearchParams({ genres: ids, page: DEFAULT_PAGE }),
    setSelectedTagIds: (ids: number[]) => updateSearchParams({ tags: ids, page: DEFAULT_PAGE }),
    toggleAttendanceMode: (value: AttendanceMode) =>
      updateSearchParams({
        attendanceModes: toggleArrayValue(attendanceModes, value),
        page: DEFAULT_PAGE,
      }),
    togglePerformerType: (value: PerformerType) =>
      updateSearchParams({
        performerTypes: toggleArrayValue(performerTypes, value),
        page: DEFAULT_PAGE,
      }),
    toggleGenreId: (id: number) =>
      updateSearchParams({ genres: toggleArrayValue(selectedGenreIds, id), page: DEFAULT_PAGE }),
    toggleTagId: (id: number) =>
      updateSearchParams({ tags: toggleArrayValue(selectedTagIds, id), page: DEFAULT_PAGE }),
    toggleSeriesTagId: (id: number) =>
      updateSearchParams({ tags: toggleArrayValue(selectedTagIds, id), page: DEFAULT_PAGE }),
    clearFilters: () =>
      updateSearchParams({
        attendanceModes: [],
        performerTypes: [],
        genres: [],
        tags: [],
        firstEventStartAfter: '',
        firstEventStartBefore: '',
        page: DEFAULT_PAGE,
      }),
  }
}
