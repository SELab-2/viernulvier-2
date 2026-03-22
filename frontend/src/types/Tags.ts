/**
 * Tag object returned by backend tag serializers.
 *
 * This same shape is reused when tags are nested inside a production.
 */
export interface Tag {
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
  name: Record<string, string> | null
  short_description: Record<string, string> | null
  url_title: Record<string, string> | null
}

/**
 * Paginated list response for tags.
 */
export interface TagListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Tag[]
}
