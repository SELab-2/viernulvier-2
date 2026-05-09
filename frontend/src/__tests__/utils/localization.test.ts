import { describe, expect, it } from '@jest/globals'

import { getLocalizedValue } from '../../utils/localization'

describe('getLocalizedValue', () => {
  it('returns the requested language when available', () => {
    expect(getLocalizedValue({ nl: 'Hallo', en: 'Hello' }, 'en')).toBe('Hello')
  })

  it('falls back to the first available translation when language key is missing', () => {
    expect(getLocalizedValue({ nl: 'Hallo', en: 'Hello' }, 'fr')).toBe('Hallo')
  })

  it('returns an empty string for nullish or non-object values', () => {
    expect(getLocalizedValue(undefined, 'nl')).toBe('')
    expect(getLocalizedValue(null, 'nl')).toBe('')
    expect(getLocalizedValue('not-an-object' as unknown as Record<string, string>, 'nl')).toBe('')
  })

  it('returns an empty string when object contains no values', () => {
    expect(getLocalizedValue({}, 'nl')).toBe('')
  })
})
