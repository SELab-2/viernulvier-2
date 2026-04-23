export type SearchSortTarget = 'name' | 'date'
export type SearchSortDirection = 'asc' | 'desc'
export type SearchViewMode = 'list' | 'grid'

// Default sort target options for the sort target selector in the search controls bar.
export const DEFAULT_SORT_TARGET_OPTIONS: Array<{ value: SearchSortTarget; labelKey: string }> = [
  { value: 'date', labelKey: 'searchbar.sort.date' },
  { value: 'name', labelKey: 'searchbar.sort.name' },
]
