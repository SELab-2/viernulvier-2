/**
 * Typed error thrown by the API interceptor for every failed HTTP request.
 *
 * Using a dedicated class instead of plain `Error` lets calling code
 * distinguish API errors from other runtime errors and inspect the HTTP
 * status without having to re-parse the raw Axios error.
 *
 * Common status codes you can check against:
 * - `400` — invalid query parameters or request body
 * - `401` — request lacks valid authentication
 * - `403` — authenticated but not authorised
 * - `404` — resource does not exist
 * - `500` — unhandled server-side failure
 * - `0`   — no response received (network issue / timeout)
 *
 * @example
 * try {
 *   const genre = await getGenre(id);
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     if (error.status === 404) showNotFound();
 *     if (error.status === 401) redirectToLogin();
 *   }
 * }
 */
export class ApiError extends Error {
  constructor(
    /** The HTTP status code, or `0` when no response was received. */
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

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
