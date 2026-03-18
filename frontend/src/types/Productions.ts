import type { Genre } from './Genres'

/** Valid attendance mode values. */
export type AttendanceMode = 'offline' | 'online'

/** Valid performer type values. */
export type PerformerType = 'group' | 'solo'

/**
 * Nested UIT Database classification object returned on productions.
 */
export interface ProductionClassification {
  id: number
  name: string
}

/**
 * Tag object nested inside a production response.
 */
export interface ProductionTag {
  id: number
  url: string
  source: string
  source_type: string
  type: string
  is_external: boolean
  is_enabled: boolean
  display_name: string | null
  display_short_description: string | null
  display_url_title: string | null
  name: Record<string, string>
  short_description: Record<string, string>
  url_title: Record<string, string>
}

/**
 * Production object returned by the backend `/productions/` endpoints.
 */
export interface Production {
  id: number
  attendance_mode: AttendanceMode | ''
  performer_type: PerformerType | ''
  uit_database_theme: ProductionClassification | null
  uit_database_type: ProductionClassification | null
  display_title: string | null
  display_artist_name: string | null
  title: Record<string, string>
  artist_name: Record<string, string>
  tagline: Record<string, string>
  teaser: Record<string, string>
  description: Record<string, string>
  tags: ProductionTag[]
  genres: Genre[]
}

/**
 * Paginated response shape for `GET /productions/`.
 */
export interface ProductionListResponse {
  results: Production[]
  count?: number
  next?: string | null
  previous?: string | null
}
