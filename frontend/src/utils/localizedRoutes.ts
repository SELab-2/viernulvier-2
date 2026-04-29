export const SUPPORTED_LANGUAGES = ['en', 'nl'] as const

export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export const DEFAULT_LANGUAGE: SupportedLanguage = 'nl'

type CanonicalRouteSegment = 'archive' | 'series' | 'blogs' | 'media' | 'productions'

const LOCALIZED_SEGMENTS: Record<SupportedLanguage, Record<CanonicalRouteSegment, string>> = {
  en: {
    archive: 'archive',
    series: 'series',
    blogs: 'blogs',
    media: 'media',
    productions: 'productions',
  },
  nl: {
    archive: 'archief',
    series: 'reeksen',
    blogs: 'blogs',
    media: 'media',
    productions: 'producties',
  },
}

const SEGMENT_ALIASES: Record<string, CanonicalRouteSegment> = {
  archive: 'archive',
  archief: 'archive',
  series: 'series',
  reeksen: 'series',
  blogs: 'blogs',
  media: 'media',
  productions: 'productions',
  producties: 'productions',
}

export const normalizeLanguage = (
  language: string | null | undefined,
): SupportedLanguage | null => {
  if (!language) {
    return null
  }

  const normalized = language.trim().toLowerCase().split('-')[0]
  return SUPPORTED_LANGUAGES.includes(normalized as SupportedLanguage)
    ? (normalized as SupportedLanguage)
    : null
}

export const getLanguageFromPathname = (pathname: string): SupportedLanguage | null => {
  const firstSegment = pathname.split('/')[1]
  return normalizeLanguage(firstSegment)
}

export const resolveCurrentLanguage = (
  pathname: string,
  i18nLanguage: string | null | undefined,
  i18nResolvedLanguage?: string | null,
): SupportedLanguage =>
  getLanguageFromPathname(pathname) ??
  normalizeLanguage(i18nResolvedLanguage ?? i18nLanguage) ??
  DEFAULT_LANGUAGE

export const getLocalizedSegment = (
  canonicalSegment: CanonicalRouteSegment,
  language: SupportedLanguage,
): string => LOCALIZED_SEGMENTS[language][canonicalSegment]

export const inferLanguageFromPathname = (pathname: string): SupportedLanguage | null => {
  const firstSegment = pathname.split('/').filter(Boolean)[0]
  if (!firstSegment) {
    return null
  }

  const matchingLanguages = SUPPORTED_LANGUAGES.filter(
    (language) =>
      LOCALIZED_SEGMENTS[language].archive === firstSegment ||
      LOCALIZED_SEGMENTS[language].series === firstSegment ||
      LOCALIZED_SEGMENTS[language].blogs === firstSegment ||
      LOCALIZED_SEGMENTS[language].media === firstSegment ||
      LOCALIZED_SEGMENTS[language].productions === firstSegment,
  )

  if (matchingLanguages.length === 1) {
    return matchingLanguages[0]
  }

  return null
}

const toCanonicalSegment = (segment: string): CanonicalRouteSegment | null =>
  SEGMENT_ALIASES[segment.toLowerCase()] ?? null

export const stripLanguagePrefix = (pathname: string): string => {
  const normalizedPath = pathname.startsWith('/') ? pathname : `/${pathname}`
  const segments = normalizedPath.split('/').filter(Boolean)

  if (segments.length === 0) {
    return '/'
  }

  const firstSegmentLanguage = normalizeLanguage(segments[0])
  const pathSegments = firstSegmentLanguage ? segments.slice(1) : segments

  if (pathSegments.length > 0) {
    const canonicalFirstSegment = toCanonicalSegment(pathSegments[0])
    if (canonicalFirstSegment) {
      pathSegments[0] = canonicalFirstSegment
    }
  }

  if (pathSegments.length === 0) {
    return '/'
  }

  return `/${pathSegments.join('/')}`
}

export const toLocalizedPath = (path: string, language: SupportedLanguage): string => {
  const basePath = stripLanguagePrefix(path)
  if (basePath === '/') {
    return `/${language}`
  }

  const segments = basePath.split('/').filter(Boolean)
  if (segments.length > 0) {
    const canonicalFirstSegment = toCanonicalSegment(segments[0])
    if (canonicalFirstSegment) {
      segments[0] = getLocalizedSegment(canonicalFirstSegment, language)
    }
  }

  return `/${language}/${segments.join('/')}`
}
