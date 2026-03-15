import type { FilteredListOptions } from '../ApiTypes'

/**
 * Genre object returned by the backend `/genres/` endpoints.
 */
export interface Genre {
  id: number
  type: string
  use_as: number
  name: Record<string, string> | null
  display_name: string | null
  vendor_id: string | null
}

/**
 * Paginated response shape for `GET /genres/`.
 *
 * The backend currently returns DRF pagination fields (`count`, `next`,
 * `previous`) in addition to `results`. These metadata fields are optional in
 * this interface so tests or mocks can provide only `results` when needed.
 */
export interface GenreListResponse {
  results: Genre[]
  count?: number
  next?: string | null
  previous?: string | null
}

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
