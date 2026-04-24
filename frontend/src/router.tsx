import { Box } from '@mui/material'
import { useEffect, useLayoutEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'

import Footer from './components/Footer'
import Navbar from './components/Navbar'
import BlogDetailPage from './pages/BlogDetailPage'
import BlogsPage from './pages/BlogsPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import ProductionDetailPage from './pages/ProductionDetailPage'
import ProductionsPage from './pages/ProductionsPage'
import SeriesDetailPage from './pages/SeriesDetailPage'
import SeriesPage from './pages/SeriesPage'
import { DEFAULT_LANGUAGE, normalizeLanguage, toLocalizedPath } from './utils/localizedRoutes'

type RouterProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

const ScrollToTop = () => {
  const location = useLocation()

  useLayoutEffect(() => {
    window.scrollTo({ top: 0, left: 0 })
  }, [location.pathname, location.search])

  return null
}

const LanguagePathRedirect = () => {
  const location = useLocation()
  const { i18n } = useTranslation()
  const currentLanguage =
    normalizeLanguage(i18n.resolvedLanguage ?? i18n.language) ?? DEFAULT_LANGUAGE
  const targetPath = `${toLocalizedPath(location.pathname, currentLanguage)}${location.search}${location.hash}`

  return <Navigate to={targetPath} replace />
}

type LocalizedLayoutProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

const LocalizedLayout = ({ mode, onToggleMode }: LocalizedLayoutProps) => {
  const { lang } = useParams<{ lang: string }>()
  const { i18n } = useTranslation()
  const normalizedLanguage = normalizeLanguage(lang)

  useEffect(() => {
    if (!normalizedLanguage || i18n.resolvedLanguage === normalizedLanguage) {
      return
    }

    void i18n.changeLanguage(normalizedLanguage)
  }, [i18n, normalizedLanguage])

  if (!normalizedLanguage) {
    return <LanguagePathRedirect />
  }

  const localizedPath = (path: string) => toLocalizedPath(path, normalizedLanguage)

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar mode={mode} onToggleMode={onToggleMode} />
      <Box component="main" sx={{ flexGrow: 1 }}>
        <Routes>
          <Route index element={<HomePage />} />
          <Route path="archive" element={<ProductionsPage />} />
          <Route path="productions" element={<Navigate to={localizedPath('/archive')} replace />} />
          <Route path="productions/:id" element={<ProductionDetailPage />} />
          <Route path="series" element={<SeriesPage />} />
          <Route path="series/:id" element={<SeriesDetailPage />} />
          <Route path="blogs" element={<BlogsPage />} />
          <Route path="blogs/:id" element={<BlogDetailPage />} />
          <Route path="media" element={<Navigate to={localizedPath('/archive')} replace />} />
          {/* TODO: Remove after media page is implemented */}
          <Route path="media/:id" element={<Navigate to={localizedPath('/archive')} replace />} />
          {/* TODO: Remove after media page is implemented */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Box>
      <Footer />
    </Box>
  )
}

const Router = ({ mode, onToggleMode }: RouterProps) => {
  const defaultRoot = toLocalizedPath('/', DEFAULT_LANGUAGE)

  return (
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route
          path="/:lang/*"
          element={<LocalizedLayout mode={mode} onToggleMode={onToggleMode} />}
        />
        <Route path="/" element={<Navigate to={defaultRoot} replace />} />
        <Route path="*" element={<LanguagePathRedirect />} />
      </Routes>
    </BrowserRouter>
  )
}

export default Router
