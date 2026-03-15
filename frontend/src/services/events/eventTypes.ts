import type { FilteredListOptions } from '../ApiTypes'

/**
 * Single price row nested inside an event response.
 */
export interface EventPrice {
  id: number
  event: number
  price_rank: number | null
  price_rank_display: string | null
  price: number | null
  price_display: string | null
  amount: string
  available: number
}

/**
 * Event object returned by the backend `/events/` endpoints.
 */
export interface Event {
  id: number
  production: number
  production_display: string
  hall: number | null
  hall_display: string | null
  starts_at: string | null
  ends_at: string | null
  prices: EventPrice[]
}

/**
 * Paginated response shape for `GET /events/`.
 *
 * The backend currently returns DRF pagination fields (`count`, `next`,
 * `previous`) in addition to `results`. These metadata fields are optional in
 * this interface so tests or mocks can provide only `results` when needed.
 */
export interface EventListResponse {
  results: Event[]
  count?: number
  next?: string | null
  previous?: string | null
}

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