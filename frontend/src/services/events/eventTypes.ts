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

export interface EventFilters {
  production?: number
  hall?: number
  location?: number
  starts_at_after?: string
  starts_at_before?: string
  ends_at_after?: string
  ends_at_before?: string
}