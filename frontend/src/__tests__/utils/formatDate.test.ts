import { formatDate } from '../../utils/formatDate'

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
    expect(out).toMatch(/June/)
    expect(out).toMatch(/15/)
  })

  it('formats with another locale (nl)', () => {
    const out = formatDate('2025-06-15T12:00:00.000Z', 'nl-BE')
    expect(out.length).toBeGreaterThan(0)
  })

  it('accepts calendar date ISO strings without a time component', () => {
    const out = formatDate('2025-12-01', 'en-US')
    expect(out).toMatch(/2025/)
    expect(out).toMatch(/December/)
  })
})
