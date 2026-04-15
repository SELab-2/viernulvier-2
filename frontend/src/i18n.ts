import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en/translation.json'
import nl from './locales/nl/translation.json'

const SUPPORTED_LANGUAGES = ['en', 'nl'] as const
type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

const DEFAULT_LANGUAGE: SupportedLanguage = 'nl'
const LANGUAGE_STORAGE_KEY = 'i18nextLng'

const normalizeLanguage = (language: string | null | undefined): SupportedLanguage | null => {
  if (!language) {
    return null
  }

  const normalized = language.trim().toLowerCase().split('-')[0]
  return SUPPORTED_LANGUAGES.includes(normalized as SupportedLanguage)
    ? (normalized as SupportedLanguage)
    : null
}

const getStoredLanguage = (): SupportedLanguage | null => {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    return normalizeLanguage(window.localStorage.getItem(LANGUAGE_STORAGE_KEY))
  } catch {
    return null
  }
}

const getBrowserLanguage = (): SupportedLanguage | null => {
  if (typeof navigator === 'undefined') {
    return null
  }

  return normalizeLanguage(navigator.language)
}

const getInitialLanguage = (): SupportedLanguage =>
  getStoredLanguage() ?? getBrowserLanguage() ?? DEFAULT_LANGUAGE

const persistLanguage = (language: string) => {
  if (typeof window === 'undefined') {
    return
  }

  const normalizedLanguage = normalizeLanguage(language)
  if (!normalizedLanguage) {
    return
  }

  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, normalizedLanguage)
  } catch {
    // Ignore storage failures (private mode, disabled storage, etc.).
  }
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    nl: { translation: nl },
  },
  lng: getInitialLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: SUPPORTED_LANGUAGES,
  load: 'languageOnly',
  interpolation: {
    escapeValue: false,
  },
})

i18n.on('languageChanged', persistLanguage)

export default i18n
