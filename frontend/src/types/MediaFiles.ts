/**
 * Media file object returned by the backend `/media/` endpoints.
 */
export interface MediaFile {
  id: string
  external_id: string | null
  file: string
  filename: string
  mime_type: string
  size_bytes: number | null
  file_type: 'image' | 'pdf' | 'other'
  uploaded_by: string | null
  created_at: string
}

/**
 * Paginated response shape for `GET /media/`.
 */
export interface MediaFileListResponse {
  count: number
  next: string | null
  previous: string | null
  results: MediaFile[]
}
