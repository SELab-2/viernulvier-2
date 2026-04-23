import {
  formatDate,
  formatDateTime,
  formatTime,
  getProductionDateLabel,
} from '../../utils/dateUtils'

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
  it('returns empty string when firstEventStart is null', () => {
    expect(getProductionDateLabel(null, null, 'en-US')).toBe('')
  })

  it('returns the start date when lastEventEnd is null', () => {
    expect(getProductionDateLabel('2025-06-15T12:00:00.000Z', null, 'en-US')).toMatch(/2025/)
    expect(getProductionDateLabel('2025-06-15T12:00:00.000Z', null, 'en-US')).not.toContain(' - ')
  })

  it('returns the end date when firstEventStart is null but lastEventEnd is set', () => {
    expect(getProductionDateLabel(null, '2025-06-15T12:00:00.000Z', 'en-US')).toMatch(/2025/)
    expect(getProductionDateLabel(null, '2025-06-15T12:00:00.000Z', 'en-US')).not.toContain(' - ')
  })

  it('returns a single formatted date when first and last fall on the same calendar day', () => {
    const label = getProductionDateLabel(
      '2025-06-15T12:00:00.000Z',
      '2025-06-15T14:00:00.000Z',
      'en-US',
    )
    expect(label).toMatch(/2025/)
    expect(label).not.toContain(' - ')
  })

  it('returns a range when first and last fall on different calendar days', () => {
    const label = getProductionDateLabel(
      '2025-06-15T12:00:00.000Z',
      '2025-06-20T12:00:00.000Z',
      'en-US',
    )
    expect(label).toContain(' - ')
    expect(label).toMatch(/2025/)
  })
})
