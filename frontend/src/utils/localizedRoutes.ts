export const SUPPORTED_LANGUAGES = ['en', 'nl'] as const

export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

export const DEFAULT_LANGUAGE: SupportedLanguage = 'nl'

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

export const stripLanguagePrefix = (pathname: string): string => {
  const normalizedPath = pathname.startsWith('/') ? pathname : `/${pathname}`
  const segments = normalizedPath.split('/').filter(Boolean)

  if (segments.length === 0) {
    return '/'
  }

  const firstSegmentLanguage = normalizeLanguage(segments[0])
  const pathSegments = firstSegmentLanguage ? segments.slice(1) : segments

  if (pathSegments.length === 0) {
    return '/'
  }

  return `/${pathSegments.join('/')}`
}

export const toLocalizedPath = (path: string, language: SupportedLanguage): string => {
  const basePath = stripLanguagePrefix(path)
  return basePath === '/' ? `/${language}` : `/${language}${basePath}`
}
