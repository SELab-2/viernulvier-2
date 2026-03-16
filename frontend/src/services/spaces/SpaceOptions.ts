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

import type { Hall } from '../../types/Halls'
import type { Space } from '../../types/Spaces'

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
