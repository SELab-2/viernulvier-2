import type { FilteredListOptions } from './ApiTypes'

/**
 * Build a flat query-params object from a {@link FilteredListOptions} value.
 *
 * This is the single place where the frontend pagination conventions
 * (`page`, `pageSize`) are translated to the backend query-parameter names
 * (`page`, `page_size`). Every service should use this helper instead of
 * repeating the spread logic inline.
 *
 * @param options The pagination and filter options from the service call.
 * Arrays are encoded as comma-separated values because several backend filters
 * accept multi-value query parameters in that format.
 *
 * @returns A plain object ready to pass as Axios `params`.
 */
export function buildListParams<TFilters extends object>(
  options?: FilteredListOptions<TFilters>,
): Record<string, unknown> {
  const { page, pageSize, filters } = options ?? {}

  const params: Record<string, unknown> = {
    ...(page !== undefined ? { page } : {}),
    ...(pageSize !== undefined ? { page_size: pageSize } : {}),
  }

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        params[key] = value.join(',')
      } else {
        params[key] = value
      }
    })
  }

  return params
}
