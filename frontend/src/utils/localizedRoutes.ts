/**
 * Provides language detection, normalization, and localized routing utilities.
 *
 * This module defines supported languages and maps canonical route segments
 * (e.g. "archive", "series") to their localized equivalents. It also contains
 * helpers to:
 * - Detect language from URL paths
 * - Normalize language inputs
 * - Convert between localized and canonical route segments
 * - Build localized paths for navigation
 */

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

/**
 * Normalizes a raw language input into a supported language.
 *
 * This function:
 * - Trims whitespace
 * - Converts to lowercase
 * - Extracts base language (e.g. "en-US" → "en")
 * - Validates against SUPPORTED_LANGUAGES
 *
 * @param language Raw language string (e.g. from headers, router, or i18n)
 * @returns A SupportedLanguage if valid, otherwise `null`
 */
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

/**
 * Extracts the first URL segment and attempts to interpret it as a language.
 *
 * @param pathname Full URL pathname (e.g. "/nl/archief")
 * @returns A SupportedLanguage if the first segment is a valid language, otherwise `null`
 */
export const getLanguageFromPathname = (pathname: string): SupportedLanguage | null => {
  const firstSegment = pathname.split('/')[1]
  return normalizeLanguage(firstSegment)
}

/**
 * Resolves the active language using multiple possible sources.
 *
 * Priority:
 * 1. Language inferred from URL pathname
 * 2. i18n resolved language
 * 3. i18n language fallback
 * 4. DEFAULT_LANGUAGE
 *
 * @param pathname Current URL pathname
 * @param i18nLanguage Primary i18n language (may be undefined)
 * @param i18nResolvedLanguage Resolved i18n language (higher priority than i18nLanguage)
 * @returns A guaranteed SupportedLanguage
 */
export const resolveCurrentLanguage = (
  pathname: string,
  i18nLanguage: string | null | undefined,
  i18nResolvedLanguage?: string | null,
): SupportedLanguage =>
  getLanguageFromPathname(pathname) ??
  normalizeLanguage(i18nResolvedLanguage ?? i18nLanguage) ??
  DEFAULT_LANGUAGE

/**
 * Converts a canonical route segment into its localized version.
 *
 * Example:
 * - "archive" → "archief" (nl)
 * - "archive" → "archive" (en)
 *
 * @param canonicalSegment Internal canonical route segment
 * @param language Target language
 * @returns Localized URL segment string
 */
export const getLocalizedSegment = (
  canonicalSegment: CanonicalRouteSegment,
  language: SupportedLanguage,
): string => LOCALIZED_SEGMENTS[language][canonicalSegment]

/**
 * Attempts to infer the UI language from the first path segment.
 *
 * This checks whether the first segment matches any known localized route
 * segment (archive, series, etc.) for each supported language.
 *
 * @param pathname URL pathname
 * @returns Detected SupportedLanguage or `null` if ambiguous or unknown
 */
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

/**
 * Converts a localized or alias segment back into its canonical form.
 *
 * Example:
 * - "archief" → "archive"
 * - "producties" → "productions"
 *
 * @param segment URL segment (localized or alias)
 * @returns Canonical segment or `null` if unknown
 */
const toCanonicalSegment = (segment: string): CanonicalRouteSegment | null =>
  SEGMENT_ALIASES[segment.toLowerCase()] ?? null

/**
 * Removes a language prefix from a pathname and normalizes the first segment.
 *
 * Steps:
 * - Ensures leading slash
 * - Removes language prefix if present
 * - Converts first segment back to canonical form if needed
 *
 * @param pathname Full URL pathname
 * @returns Path without language prefix
 */
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

/**
 * Converts a canonical path into a fully localized path.
 *
 * Steps:
 * - Strips existing language prefix
 * - Replaces first segment with localized equivalent
 * - Prefixes the target language
 *
 * @param path Input path (localized or canonical)
 * @param language Target language
 * @returns Fully localized pathname
 */
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