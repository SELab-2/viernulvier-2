import { useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { SearchSortDirection, SearchSortTarget, SearchViewMode } from './types'

const DEFAULT_SEARCH_SORT_TARGET: SearchSortTarget = 'date'
const DEFAULT_SEARCH_SORT_DIRECTION: SearchSortDirection = 'desc'
const DEFAULT_SEARCH_VIEW_MODE: SearchViewMode = 'grid'
const DEFAULT_PAGE = 1

const PARAM_QUERY = 'q'
const PARAM_SORT_TARGET = 'st'
const PARAM_SORT_DIRECTION = 'sd'
const PARAM_VIEW = 'v'
const PARAM_PAGE = 'p'

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

type UpdateSearchParamsInput = {
  q?: string
  sortTarget?: SearchSortTarget
  sortDirection?: SearchSortDirection
  view?: SearchViewMode
  page?: number
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
  setSearchValue: (value: string) => void
  setSortTarget: (value: SearchSortTarget) => void
  setSortDirection: (value: SearchSortDirection) => void
  setViewMode: (value: SearchViewMode) => void
  setPage: (value: number) => void
}

export const useSearchBarUrlState = ({
  isMobile,
}: UseSearchBarUrlStateOptions): SearchBarUrlState => {
  const [searchParams, setSearchParams] = useSearchParams()

  const searchValue = searchParams.get(PARAM_QUERY) ?? ''
  const sortTarget = parseSearchSortTarget(searchParams.get(PARAM_SORT_TARGET))
  const sortDirection = parseSearchSortDirection(searchParams.get(PARAM_SORT_DIRECTION))
  const parsedViewMode = parseSearchViewMode(searchParams.get(PARAM_VIEW))
  const page = parsePage(searchParams.get(PARAM_PAGE))
  const viewMode: SearchViewMode = isMobile ? DEFAULT_SEARCH_VIEW_MODE : parsedViewMode

  const updateSearchParams = useCallback(
    ({
      q,
      sortTarget: nextSortTarget,
      sortDirection: nextSortDirection,
      view,
      page: nextPage,
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
    page,
    // Any search/sort/layout change can affect result ordering, so we reset to page 1.
    setSearchValue: (value: string) => updateSearchParams({ q: value.trim(), page: DEFAULT_PAGE }),
    setSortTarget: (value: SearchSortTarget) =>
      updateSearchParams({ sortTarget: value, page: DEFAULT_PAGE }),
    setSortDirection: (value: SearchSortDirection) =>
      updateSearchParams({ sortDirection: value, page: DEFAULT_PAGE }),
    setViewMode: (value: SearchViewMode) => updateSearchParams({ view: value }),
    setPage: (value: number) => updateSearchParams({ page: value }),
  }
}
