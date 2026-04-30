import {
  inferLanguageFromPathname,
  normalizeLanguage,
  resolveCurrentLanguage,
  stripLanguagePrefix,
  toLocalizedPath,
} from '../../utils/localizedRoutes'

describe('normalizeLanguage', () => {
  it('normalizes language variants to supported language codes', () => {
    expect(normalizeLanguage('EN-us')).toBe('en')
    expect(normalizeLanguage(' nl ')).toBe('nl')
  })

  it('returns null for unsupported or empty values', () => {
    expect(normalizeLanguage('fr')).toBeNull()
    expect(normalizeLanguage('')).toBeNull()
    expect(normalizeLanguage(null)).toBeNull()
    expect(normalizeLanguage(undefined)).toBeNull()
  })
})

describe('inferLanguageFromPathname', () => {
  it('infers language from unique localized slugs', () => {
    expect(inferLanguageFromPathname('/archive')).toBe('en')
    expect(inferLanguageFromPathname('/archief')).toBe('nl')
    expect(inferLanguageFromPathname('/reeksen')).toBe('nl')
    expect(inferLanguageFromPathname('/producties/42')).toBe('nl')
  })

  it('returns null when slug is shared or unknown', () => {
    expect(inferLanguageFromPathname('/blogs')).toBeNull()
    expect(inferLanguageFromPathname('/unknown')).toBeNull()
    expect(inferLanguageFromPathname('/')).toBeNull()
  })
})

describe('stripLanguagePrefix', () => {
  it('strips supported language prefix and canonicalizes localized slugs', () => {
    expect(stripLanguagePrefix('/en/archive')).toBe('/archive')
    expect(stripLanguagePrefix('/nl/archief')).toBe('/archive')
    expect(stripLanguagePrefix('/nl/reeksen/96')).toBe('/series/96')
  })

  it('handles trailing slashes and root language routes', () => {
    expect(stripLanguagePrefix('/nl/archief/')).toBe('/archive')
    expect(stripLanguagePrefix('/en')).toBe('/')
  })

  it('keeps unknown first segments untouched', () => {
    expect(stripLanguagePrefix('/fr/archive')).toBe('/fr/archive')
  })
})

describe('toLocalizedPath', () => {
  it('converts canonical paths to localized language paths', () => {
    expect(toLocalizedPath('/archive', 'nl')).toBe('/nl/archief')
    expect(toLocalizedPath('/series/96', 'nl')).toBe('/nl/reeksen/96')
    expect(toLocalizedPath('/nl/archief', 'en')).toBe('/en/archive')
  })

  it('normalizes root and trailing slash paths', () => {
    expect(toLocalizedPath('/', 'en')).toBe('/en')
    expect(toLocalizedPath('/nl/reeksen/', 'en')).toBe('/en/series')
  })

  it('keeps unknown slugs while applying language prefix', () => {
    expect(toLocalizedPath('/fr/archive', 'nl')).toBe('/nl/fr/archive')
  })
})

describe('resolveCurrentLanguage', () => {
  it('prefers language from pathname prefix', () => {
    expect(resolveCurrentLanguage('/en/archive', 'nl', 'nl')).toBe('en')
  })

  it('falls back to i18n resolved language when pathname has no language prefix', () => {
    expect(resolveCurrentLanguage('/archive', 'nl', 'en')).toBe('en')
  })

  it('falls back to default language when neither path nor i18n can resolve', () => {
    expect(resolveCurrentLanguage('/archive', 'fr', 'fr')).toBe('nl')
  })
})
