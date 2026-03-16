/**
 * Space object returned by the backend `/spaces/` endpoints.
 */
import type { Hall } from './Halls'
import type { Location } from './Locations'

export interface Space {
  id: number
  location: Location
  name: Record<string, string> | null
  display_name: string | null
  halls: Hall[]
}

/**
 * Paginated response shape for `GET /spaces/`.
 */
export interface SpaceListResponse {
  results: Space[]
  count?: number
  next?: string | null
  previous?: string | null
}
