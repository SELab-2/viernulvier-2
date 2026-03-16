import { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/spaces/` list endpoint.
 */
export interface SpaceFilters {
  location?: number
  name?: string
}

/**
 * Options accepted by {@link getSpaces}.
 */
export type GetSpacesOptions = FilteredListOptions<SpaceFilters>
