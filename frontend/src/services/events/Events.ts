import type { Event, EventListResponse } from '../../types/Events'
import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetEventsOptions } from './EventOptions'

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
 * const event = await getEvent(12);
 *
 * @throws {ApiError} When the request fails.
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
 * - `production`: filter by parent production ID
 * - `hall`: filter by hall ID
 * - `location`: filter by parent location ID
 * - `starts_at_after`: filter to events starting on or after an ISO datetime
 * - `starts_at_before`: filter to events starting on or before an ISO datetime
 * - `ends_at_after`: filter to events ending on or after an ISO datetime
 * - `ends_at_before`: filter to events ending on or before an ISO datetime
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `starts_at` or `-starts_at`
 * - `external_id`: external identifier, for example `api/v1/events/123`
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
 *     production: 42,
 *     starts_at_after: '2026-01-01T00:00:00Z',
 *     ordering: 'starts_at',
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getEvents = async (options?: GetEventsOptions): Promise<EventListResponse> => {
  const res = await api.get<EventListResponse>('/events/', {
    params: buildListParams(options),
  })
  return res.data
}
