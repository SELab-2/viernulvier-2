import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/productions/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface ProductionFilters {
  attendance_mode?: string
  performer_type?: string
  uit_database_theme?: number
  uit_database_type?: number
  genre?: number
  tag?: number
  has_media?: boolean
  title?: string
  artist_name?: string
}

/**
 * Options accepted by {@link getProductions}.
 *
 * Combines pagination (`page`, `pageSize`), production-specific filters
 * ({@link ProductionFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetProductionsOptions = FilteredListOptions<ProductionFilters>
