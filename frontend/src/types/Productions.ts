import type { BlogCardData } from './Blogs'
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
  media_gallery: MediaGallery
  first_event_start: string | null
  last_event_end: string | null
  tags: Tag[]
  genres: Genre[]
}

/** Shape of a single related entry (grouped by tag). */
export interface ProductionRelated {
  tag: RelatedTag
  productions: RelatedProduction[]
}

/**
 * Production object returned by the backend `/productions/` endpoints.
 * Inherits from `RelatedProduction` and adds some fields for detail view.
 * Note: some fields like `artist_name` are duplicated here because they are
 *       not guaranteed to be present in the `related` entries.
 */
export interface Production extends RelatedProduction {
  tagline: Record<string, string>
  teaser: Record<string, string>
  description: Record<string, string>
  uit_database_type?: ProductionClassification | null
  performer_type?: PerformerType | ''
  attendance_mode?: AttendanceMode | ''
  events?: Event[]
  related?: ProductionRelated[]
  video_1?: Record<string, string>
  video_2?: Record<string, string>
  genres: Genre[]
  blogs?: BlogCardData[]
  artist_name: Record<string, string> | null
  display_artist_name: string | null
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
