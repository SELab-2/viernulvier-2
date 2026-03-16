import type { Genre } from './Genres'
import type { Tag } from './Tag'

/**
 * Minimal taxonomy entry used for production classification.
 */
export interface ProductionTaxonomy {
  id: number
  name: string
}

/**
 * Production object nested inside an event response.
 */
export interface Production {
  id: number
  attendance_mode: string
  performer_type: string
  uit_database_theme: ProductionTaxonomy | null
  uit_database_type: ProductionTaxonomy | null
  display_title: string | null
  display_artist_name: string | null
  title: Record<string, string> | null
  artist_name: Record<string, string> | null
  tagline: Record<string, string> | null
  teaser: Record<string, string> | null
  description: Record<string, string> | null
  tags: Tag[]
  genres: Genre[]
}
