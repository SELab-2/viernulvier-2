import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/halls/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
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
 *
 * Combines pagination (`page`, `pageSize`), hall-specific filters
 * ({@link HallFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetHallsOptions = FilteredListOptions<HallFilters>
