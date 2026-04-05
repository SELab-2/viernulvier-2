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
}

type UseSearchBarUrlStateOptions = {
  isMobile: boolean
}

export type SearchBarUrlState = {
  searchValue: string
  sortTarget: SearchSortTarget
  sortDirection: SearchSortDirection
  viewMode: SearchViewMode
  setSearchValue: (value: string) => void
  setSortTarget: (value: SearchSortTarget) => void
  setSortDirection: (value: SearchSortDirection) => void
  setViewMode: (value: SearchViewMode) => void
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

  const updateSearchParams = useCallback(
    ({
      q,
      sortTarget: nextSortTarget,
      sortDirection: nextSortDirection,
      view,
    }: UpdateSearchParamsInput) => {
      setSearchParams(
        (currentParams) => {
          const nextParams = new URLSearchParams(currentParams)

          if (q !== undefined) {
            const normalizedQ = q.trim()
            if (normalizedQ) {
              nextParams.set(PARAM_QUERY, normalizedQ)
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
    setSearchValue: (value: string) => updateSearchParams({ q: value }),
    setSortTarget: (value: SearchSortTarget) => updateSearchParams({ sortTarget: value }),
    setSortDirection: (value: SearchSortDirection) => updateSearchParams({ sortDirection: value }),
    setViewMode: (value: SearchViewMode) => updateSearchParams({ view: value }),
  }
}
