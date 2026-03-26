import type { Event } from './Events'
import type { Genre } from './Genres'
import type { MediaGallery } from './Media'
import type { Tag } from './Tags'
import { MediaGallery } from './Media'

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
 * Production object returned by the backend `/productions/` endpoints.
 */
export interface Production {
  id: number
  attendance_mode: AttendanceMode | ''
  performer_type: PerformerType | ''
  media_gallery: MediaGallery | null
  uit_database_theme: ProductionClassification | null
  uit_database_type: ProductionClassification | null
  display_title: string | null
  display_artist_name: string | null
  title: Record<string, string>
  artist_name: Record<string, string>
  tagline: Record<string, string>
  teaser: Record<string, string>
  description: Record<string, string>
  tags: Tag[]
  genres: Genre[]
  media_gallery: MediaGallery
  events?: Event[]
}

/**
 * Paginated response shape for `GET /productions/`.
 */
export interface ProductionListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Production[]
}
