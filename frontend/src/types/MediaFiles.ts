/**
 * Translation dictionary keyed by language code.
 *
 * Example: `{ nl: 'Nederlandse brochure', en: 'English brochure' }`
 */
export type MediaFileDescriptionTranslations = Record<string, string>

/**
 * Media file object returned by the backend `/media-files/` endpoints.
 */
export interface MediaFile {
  id: string
  external_id: string | null
  file: string
  filename: string
  display_description: string | null
  description: MediaFileDescriptionTranslations
  mime_type: string
  size_bytes: number
  file_type: 'image' | 'pdf' | 'other'
  created_at: string
}

/**
 * Paginated response shape for `GET /media-files/`.
 */
export interface MediaFileListResponse {
  count: number
  next: string | null
  previous: string | null
  results: MediaFile[]
}
