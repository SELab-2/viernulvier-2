import type { ListResponse } from '../types/Common'

/**
 * Fetch all pages of any paginated list endpoint.
 *
 * @param fetcher A function that accepts `(page, pageSize, options)` and returns a paginated list response.
 * @param options Optional filters/settings forwarded to every page request.
 * @param pageSize Items per request - larger = fewer round-trips.
 * @returns A promise that resolves to all items across all pages.
 *
 * @example
 * const allGenres = await fetchAllPages(
 *   (page, pageSize, options) => getGenres({ page, pageSize, ...options }),
 * )
 *
 * @example
 * const filteredGenres = await fetchAllPages(
 *   (page, pageSize, options) => getGenres({ page, pageSize, ...options }),
 *   { filters: { type: 'theater' } },
 * )
 */
export async function fetchAllPages<T, O extends object = object>(
    fetcher: (page: number, pageSize: number, options?: O) => Promise<ListResponse<T>>,
    options?: O,
    pageSize = 100,
): Promise<T[]> {
    const results: T[] = []
    let page = 1

    while (true) {
        const res = await fetcher(page, pageSize, options)
        results.push(...res.results)

        if (!res.next) {
            break
        }
        page++
    }

    return results
}
