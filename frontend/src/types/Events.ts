import type { Hall } from './Halls'
import type { Price, PriceRank } from './Price'
import type { Production } from './Production'

/**
 * Single price row nested inside an event response.
 */
export interface EventPrice {
  id: number
  event: number
  price_rank: PriceRank | null
  price_rank_display: string | null
  price: Price | null
  price_display: string | null
  amount: string
  available: number
}

/**
 * Event object returned by the backend `/events/` endpoints.
 */
export interface Event {
  id: number
  production: Production
  production_display: string | null
  hall: Hall | null
  hall_display: string | null
  starts_at: string | null
  ends_at: string | null
  prices: EventPrice[]
}

/**
 * Paginated response shape for `GET /events/`.
 */
export interface EventListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Event[]
}
