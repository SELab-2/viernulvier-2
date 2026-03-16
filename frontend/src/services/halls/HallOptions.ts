import { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/halls/` list endpoint.
 */
export interface HallFilters {
  space?: number
  location?: number
  seat_selection?: boolean
  open_seating?: boolean
  name?: string
}

/**
 * Options accepted by {@link getHalls}.
 */
export type GetHallsOptions = FilteredListOptions<HallFilters>
