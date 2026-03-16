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
 */
export interface EventListResponse {
  results: Event[]
  count?: number
  next?: string | null
  previous?: string | null
}
