/**
 * Hall object returned by the backend `/halls/` endpoints.
 */
import type { Space } from './Spaces'

export interface Hall {
  id: number
  space: Space | null
  seat_selection: boolean
  open_seating: boolean
  name: Record<string, string> | null
  display_name: string | null
  remark: Record<string, string> | null
}

/**
 * Paginated response shape for `GET /halls/`.
 */
export interface HallListResponse {
  results: Hall[]
  count?: number
  next?: string | null
  previous?: string | null
}
