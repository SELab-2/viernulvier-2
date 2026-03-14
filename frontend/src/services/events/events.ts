import { api } from '../api'
import type { FilteredListOptions } from '../apiTypes'
import type { Event, EventFilters } from '../events/eventTypes'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * Fetch a paginated list of events.
 *
 * Supports pagination, search, ordering, and event-specific filters.
 */
export async function getEvents(
  options: FilteredListOptions<EventFilters> = {},
): Promise<PaginatedResponse<Event>> {
  const params: Record<string, string | number> = {}

  if (options.page !== undefined) {
    params.page = options.page
  }

  if (options.pageSize !== undefined) {
    params.page_size = options.pageSize
  }

  if (options.filters) {
    Object.entries(options.filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params[key] = value
      }
    })
  }

  const response = await api.get<PaginatedResponse<Event>>('/events/', { params })
  return response.data
}

/**
 * Fetch a single event by id.
 */
export async function getEvent(id: number | string): Promise<Event> {
  const response = await api.get<Event>(`/events/${id}/`)
  return response.data
}