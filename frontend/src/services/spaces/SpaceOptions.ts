import { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/spaces/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface SpaceFilters {
  location?: number
  name?: string
}

/**
 * Options accepted by {@link getSpaces}.
 *
 * Combines pagination (`page`, `pageSize`), space-specific filters
 * ({@link SpaceFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetSpacesOptions = FilteredListOptions<SpaceFilters>
