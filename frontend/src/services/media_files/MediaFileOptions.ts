import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/media/` list endpoint.
 *
 * These are combined with the shared {@link CommonListFilters} (`search`,
 * `ordering`, `external_id`) that every list endpoint supports.
 */
export interface MediaFileFilters {
  file_type?: 'image' | 'pdf' | 'other'
  mime_type?: string
  filename?: string
  uploaded_by?: string
}

/**
 * Options accepted by {@link getMediaFiles}.
 *
 * Combines pagination (`page`, `pageSize`), media-file-specific filters
 * ({@link MediaFileFilters}), and shared list filters (`search`, `ordering`,
 * `external_id`).
 */
export type GetMediaFilesOptions = FilteredListOptions<MediaFileFilters>
