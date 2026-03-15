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
    Object.assign(params, filters)
  }

  return params
}