import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/genres/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface GenreFilters {
  use_as?: number
  type?: string
  vendor_id?: string
  name?: string
}

/**
 * Options accepted by {@link getGenres}.
 *
 * Combines pagination (`page`, `pageSize`), genre-specific filters
 * ({@link GenreFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetGenresOptions = FilteredListOptions<GenreFilters>
