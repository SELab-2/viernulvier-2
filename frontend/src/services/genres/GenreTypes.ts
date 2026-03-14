import type { FilteredListOptions } from '../ApiTypes'

export interface GenreFilters {
  use_as?: number
  type?: string
  vendor_id?: string
  name?: string
}

export type GetGenresOptions = FilteredListOptions<GenreFilters>
