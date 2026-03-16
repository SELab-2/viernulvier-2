import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/locations/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface LocationFilters {
  city?: string
  country?: string
  postal_code?: string
  is_own_location?: boolean
  name?: string
}

/**
 * Options accepted by {@link getLocations}.
 *
 * Combines pagination (`page`, `pageSize`), location-specific filters
 * ({@link LocationFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetLocationsOptions = FilteredListOptions<LocationFilters>
