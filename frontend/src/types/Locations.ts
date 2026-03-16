/**
 * Location object returned by the backend `/locations/` endpoints.
 */
export interface Location {
  id: number
  street: string | null
  number: string | null
  postal_code: string | null
  city: string | null
  country: string
  phone_1: string | null
  phone_2: string | null
  is_own_location: boolean
  name: Record<string, string> | null
  display_name: string | null
}

/**
 * Paginated response shape for `GET /locations/`.
 *
 * The backend currently returns DRF pagination fields (`count`, `next`,
 * `previous`) in addition to `results`. These metadata fields are optional in
 * this interface so tests or mocks can provide only `results` when needed.
 */
export interface LocationListResponse {
  results: Location[]
  count?: number
  next?: string | null
  previous?: string | null
}
