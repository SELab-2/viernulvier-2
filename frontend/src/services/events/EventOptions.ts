import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/events/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface EventFilters {
  production?: number
  hall?: number
  location?: number
  starts_at_after?: string
  starts_at_before?: string
  ends_at_after?: string
  ends_at_before?: string
}

/**
 * Options accepted by {@link getEvents}.
 *
 * Combines pagination (`page`, `pageSize`), event-specific filters
 * ({@link EventFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetEventsOptions = FilteredListOptions<EventFilters>
