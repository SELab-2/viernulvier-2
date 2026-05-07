import type { Production } from './Productions'

/**
 * Minimal blog fields required for blog cards and related blog sections.
 */
export interface BlogCardData {
  id: number
  slug: string
  published_at: string | null
  cover_image: string | null
  title: Record<string, string>
  excerpt: Record<string, string>
  display_title: string
  display_excerpt: string
}

/**
 * Blog object returned by the backend `/blogs/` endpoints.
 */
export interface Blog extends BlogCardData {
  body: Record<string, string>
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
