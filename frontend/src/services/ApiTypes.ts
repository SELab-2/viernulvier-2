/**
 * Reusable pagination options for list endpoints.
 *
 * Extend or compose this type whenever an API endpoint supports paginated
 * results and should accept a page number and page size.
 */
export interface PaginationOptions {
  page?: number
  pageSize?: number
}

/**
 * Query parameters that are supported by all list endpoints in the API.
 *
 * These values are sent inside the `filters` object and are forwarded as
 * query parameters by the service layer.
 */
export interface CommonListFilters {
  /**
   * Free-text search term used by the backend search integration.
   */
  search?: string

  /**
   * Ordering expression, for example `name` or `-created_at`.
   */
  ordering?: string

  /**
   * External resource identifier, for example `/genres/123`.
   */
  external_id?: string
}

/**
 * Generic list-query options that combine pagination with endpoint-specific
 * filter fields.
 *
 * @typeParam TFilters The filter shape for a specific endpoint.
 */
export interface FilteredListOptions<TFilters = Record<string, never>> extends PaginationOptions {
  filters?: TFilters & CommonListFilters
}
