import type { Event } from '../../types/Events'
import {
  formatDate,
  formatDateTime,
  formatTime,
  getProductionDateLabel,
} from '../../utils/dateUtils'

function eventWithStartsAt(starts_at: string | null): Event {
  return { starts_at } as Event
}

describe('formatDate', () => {
  it('returns empty string for null', () => {
    expect(formatDate(null, 'nl-BE')).toBe('')
  })

  it('returns empty string for undefined', () => {
    expect(formatDate(undefined, 'nl-BE')).toBe('')
  })

  it('returns empty string for invalid ISO date', () => {
    expect(formatDate('not-a-date', 'nl-BE')).toBe('')
  })

  it('formats a valid ISO date with the given locale', () => {
    const out = formatDate('2025-06-15T12:00:00.000Z', 'en-US')
    expect(out).toMatch(/2025/)
    expect(out).toMatch(/jun/i)
    expect(out).toMatch(/15/)
  })

  it('formats with another locale (nl)', () => {
    const out = formatDate('2025-06-15T12:00:00.000Z', 'nl-BE')
    expect(out.length).toBeGreaterThan(0)
  })

  it('accepts calendar date ISO strings without a time component', () => {
    const out = formatDate('2025-12-01', 'en-US')
    expect(out).toMatch(/2025/)
    expect(out).toMatch(/dec/i)
  })

  it('formatTime returns empty string for null', () => {
    expect(formatTime(null, 'nl-BE')).toBe('')
  })

  it('formatTime returns empty string for invalid ISO time', () => {
    expect(formatTime('not-a-date', 'nl-BE')).toBe('')
  })

  it('formatTime formats a valid ISO datetime', () => {
    const out = formatTime('2025-06-15T12:00:00.000Z', 'en-US')
    expect(out).toMatch(/\d{1,2}:\d{2}/)
  })

  it('formatDateTime returns empty string for null', () => {
    expect(formatDateTime(null, 'nl-BE')).toBe('')
  })

  it('formatDateTime returns empty string for invalid ISO date-time', () => {
    expect(formatDateTime('not-a-date', 'nl-BE')).toBe('')
  })

  it('formatDateTime formats a valid ISO datetime', () => {
    const out = formatDateTime('2025-06-15T12:00:00.000Z', 'en-US')
    expect(out).toMatch(/2025/)
    expect(out).toMatch(/\d{1,2}:\d{2}/)
  })
})

describe('getProductionDateLabel', () => {
  it('returns empty string when events is undefined', () => {
    expect(getProductionDateLabel(undefined, 'en-US')).toBe('')
  })

  it('returns empty string when events is empty', () => {
    expect(getProductionDateLabel([], 'en-US')).toBe('')
  })

  it('returns empty string when no event has starts_at', () => {
    expect(getProductionDateLabel([eventWithStartsAt(null)], 'en-US')).toBe('')
  })

  it('returns a single formatted date for one event', () => {
    const label = getProductionDateLabel([eventWithStartsAt('2025-06-15T12:00:00.000Z')], 'en-US')
    expect(label).toMatch(/2025/)
    expect(label).not.toContain(' - ')
  })

  it('returns a range when first and last events differ by calendar day', () => {
    const label = getProductionDateLabel(
      [
        eventWithStartsAt('2025-06-15T12:00:00.000Z'),
        eventWithStartsAt('2025-06-20T12:00:00.000Z'),
      ],
      'en-US',
    )
    expect(label).toContain(' - ')
    expect(label).toMatch(/2025/)
  })

  it('uses earliest and latest by starts_at when events are out of order', () => {
    const label = getProductionDateLabel(
      [
        eventWithStartsAt('2025-06-20T12:00:00.000Z'),
        eventWithStartsAt('2025-06-15T12:00:00.000Z'),
      ],
      'en-US',
    )
    expect(label).toContain(' - ')
  })
})
