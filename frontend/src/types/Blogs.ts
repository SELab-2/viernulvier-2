import type { Production } from './Productions'

/**
 * Blog object returned by the backend `/blogs/` endpoints.
 */
export interface Blog {
  id: number
  slug: string
  published_at: string | null
  cover_image: string | null
  title: Record<string, string>
  body: Record<string, string>
  excerpt: Record<string, string>
  display_title: string
  display_excerpt: string
  productions: Production[]
}

/**
 * Paginated response shape for `GET /blogs/`.
 */
export interface BlogListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Blog[]
}
