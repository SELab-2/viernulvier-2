import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { Event, EventListResponse } from '../../types/Events'
import type { GetEventsOptions } from './EventOptions'

/**
 * Retrieve a single event by its numeric ID.
 */
export const getEvent = async (id: number): Promise<Event> => {
  const res = await api.get<Event>(`/events/${id}/`)
  return res.data
}

/**
 * Retrieve a list of events with optional pagination and filtering.
 */
export const getEvents = async (options?: GetEventsOptions): Promise<EventListResponse> => {
  const res = await api.get<EventListResponse>('/events/', {
    params: buildListParams(options),
  })
  return res.data
}
