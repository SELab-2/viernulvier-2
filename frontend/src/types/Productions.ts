import type { Event } from './Events'
import type { Genre } from './Genres'
import type { MediaGallery } from './Media'
import type { Tag } from './Tags'

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

/** Tag returned inside a `related` entry. */
export interface RelatedTag {
  id: number
  name: Record<string, string>
  display_name: string | null
}

/** Minimal production shape used under `related` entries. */
export interface RelatedProduction {
  id: number
  title: Record<string, string>
  display_title: string | null
  artist_name: Record<string, string> | null
  display_artist_name: string | null
  media_gallery: MediaGallery
}

/** Shape of a single related entry (grouped by tag). */
export interface ProductionRelated {
  tag: RelatedTag
  productions: RelatedProduction[]
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
  tags: Tag[]
  genres: Genre[]
  media_gallery: MediaGallery
  events?: Event[]
  first_event_start: string | null
  last_event_end: string | null
  related?: ProductionRelated[]
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
