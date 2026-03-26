import { getTranslatedRecord } from '../../utils/translations'

describe('getTranslatedRecord', () => {
  it('returns empty string when record is null', () => {
    expect(getTranslatedRecord(null, 'nl')).toBe('')
  })

  it('returns empty string when record is undefined', () => {
    expect(getTranslatedRecord(undefined, 'nl')).toBe('')
  })

  it('returns empty string when record is an empty object', () => {
    expect(getTranslatedRecord({}, 'nl')).toBe('')
  })

  it('returns the translation for the current language when present', () => {
    expect(getTranslatedRecord({ nl: 'Hallo', en: 'Hello' }, 'nl')).toBe('Hallo')
    expect(getTranslatedRecord({ nl: 'Hallo', en: 'Hello' }, 'en')).toBe('Hello')
  })

  it('returns the explicit fallback when the language key is missing', () => {
    expect(getTranslatedRecord({ en: 'Hello' }, 'nl', 'Default')).toBe('Default')
  })

  it('uses empty string as fallback when third argument is omitted and key is missing', () => {
    expect(getTranslatedRecord({ en: 'Hello' }, 'nl')).toBe('')
  })

  it('treats explicit null fallback as empty string', () => {
    expect(getTranslatedRecord({ en: 'Hello' }, 'nl', null)).toBe('')
  })

  it('uses display fallback when record is empty and fallback is provided', () => {
    expect(getTranslatedRecord(null, 'nl', 'Display')).toBe('Display')
  })

  it('falls back when the language key exists but the value is empty', () => {
    expect(getTranslatedRecord({ nl: '' }, 'nl', 'Fallback')).toBe('Fallback')
  })

  it('prefers a non-empty translation over the display fallback', () => {
    expect(getTranslatedRecord({ nl: 'Vertaald' }, 'nl', 'Display')).toBe('Vertaald')
  })
})
