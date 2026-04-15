import type { Hall } from '../../types/Halls'
import type { Space } from '../../types/Spaces'
import type { FilteredListOptions } from '../ApiTypes'

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

/**
 * Internal: shape of a hall as nested in a space response (no `space` field).
 */
export type HallInSpaceResponse = Omit<Hall, 'space'>

/**
 * Internal: shape of a space as returned by the backend (halls are nested, not full Hall[]).
 */
export type SpaceResponse = Omit<Space, 'halls'> & {
  halls: HallInSpaceResponse[]
}
