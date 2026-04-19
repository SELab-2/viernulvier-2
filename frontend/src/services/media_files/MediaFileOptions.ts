import type { FilteredListOptions } from '../ApiTypes'

/**
 * Endpoint-specific filter fields for the `/media-files/` list endpoint.
 *
 * These are combined with the shared list filters (`search`, `ordering`,
 * `external_id`) that every list endpoint supports.
 */
export interface MediaFileFilters {
  /** Case-insensitive exact match on normalized file type. */
  file_type?: 'image' | 'pdf' | 'other'
  /** Case-insensitive exact match on MIME type. */
  mime_type?: string
  /** Case-insensitive substring match on the original uploaded filename. */
  filename?: string
  /** Case-insensitive substring match across translated descriptions. */
  description?: string
}

/**
 * Options accepted by `getMediaFiles`.
 *
 * Combines pagination (`page`, `pageSize`), media-file-specific filters, and
 * shared list filters (`search`, `ordering`, `external_id`).
 */
export type GetMediaFilesOptions = FilteredListOptions<MediaFileFilters>
