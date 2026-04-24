import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en/translation.json'
import nl from './locales/nl/translation.json'
import {
  DEFAULT_LANGUAGE,
  SUPPORTED_LANGUAGES,
  type SupportedLanguage,
} from './utils/localizedRoutes'

const initialLanguage: SupportedLanguage = DEFAULT_LANGUAGE

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    nl: { translation: nl },
  },
  lng: initialLanguage,
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: SUPPORTED_LANGUAGES,
  load: 'languageOnly',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
