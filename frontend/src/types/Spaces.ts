/**
 * Space object returned by the backend `/spaces/` endpoints.
 */
export interface Space {
  id: number
  location: number
  name: Record<string, string> | null
  display_name: string | null
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
