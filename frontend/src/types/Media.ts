/** Named crop variant of a MediaItem (e.g. thumbnail, banner). */
export interface MediaItemCrop {
  id: number
  name: string
  image_url: string | null
}

/**
 * A single media asset within a MediaGallery.
 * Translated fields return all available translations as language-code
 * dictionaries (e.g. { en: 'Poster', fr: 'Affiche' }).
 */
export interface MediaItem {
  id: number
  gallery: number | null
  type: 'foto' | 'video' | 'audio' | 'other'
  format: string
  original_filename: string
  position: number
  width: number | null
  height: number | null
  title: Record<string, string> | null
  display_title: string | null
  description: Record<string, string> | null
  credits: Record<string, string> | null
  link: Record<string, string> | null
  crops: MediaItemCrop[]
}

/** A named collection of MediaItems. */
export interface MediaGallery {
  id: number
  name: string | null
  media_items: MediaItem[]
}

export interface MediaGalleryListResponse {
  count: number
  next: string | null
  previous: string | null
  results: MediaGallery[]
}

export interface MediaItemListResponse {
  count: number
  next: string | null
  previous: string | null
  results: MediaItem[]
}
