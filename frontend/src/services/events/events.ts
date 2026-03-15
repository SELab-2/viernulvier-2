import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { Event, EventListResponse, GetEventsOptions } from './EventTypes'

/**
 * Retrieve a single event by its numeric ID.
 *
 * This sends a `GET /events/:id/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param id The unique ID of the event that should be fetched.
 * @returns A promise that resolves to the event data returned by the API.
 *
 * @example
 * const event = await getEvent(42);
 */
export const getEvent = async (id: number): Promise<Event> => {
  const res = await api.get<Event>(`/events/${id}/`)
  return res.data
}

/**
 * Retrieve a list of events with optional pagination and filtering.
 *
 * This sends a `GET /events/` request. The `options` object is translated into
 * query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported event-specific filter fields currently include:
 * - `production`: filter by production ID
 * - `hall`: filter by hall ID
 * - `location`: filter by location ID
 * - `starts_at_after`: events starting on or after the given datetime
 * - `starts_at_before`: events starting on or before the given datetime
 * - `ends_at_after`: events ending on or after the given datetime
 * - `ends_at_before`: events ending on or before the given datetime
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `starts_at` or `-starts_at`
 * - `external_id`: external identifier, when supported by the backend
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const events = await getEvents();
 *
 * @example
 * const events = await getEvents({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     production: 12,
 *     location: 3,
 *     ordering: '-starts_at',
 *   },
 * });
 */
export const getEvents = async (
  options?: GetEventsOptions,
): Promise<EventListResponse> => {
  const res = await api.get<EventListResponse>('/events/', {
    params: buildListParams(options),
  })
  return res.data
}