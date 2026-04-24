import { Box } from '@mui/material'
import { useLayoutEffect } from 'react'
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
import {
  DEFAULT_LANGUAGE,
  getLocalizedSegment,
  inferLanguageFromPathname,
  normalizeLanguage,
  resolveCurrentLanguage,
  toLocalizedPath,
} from './utils/localizedRoutes'

import type { ModeToggleProps } from './types/Theme'

const ScrollToTop = () => {
  const location = useLocation()

  useLayoutEffect(() => {
    window.scrollTo({ top: 0, left: 0 })
  }, [location.pathname, location.search])

  return null
}

type LanguagePathRedirectProps = {
  sourcePathname?: string
}

const LanguagePathRedirect = ({ sourcePathname }: LanguagePathRedirectProps) => {
  const location = useLocation()
  const { i18n } = useTranslation()
  const redirectSourcePath = sourcePathname ?? location.pathname
  const inferredLanguage = inferLanguageFromPathname(redirectSourcePath)
  const currentLanguage =
    inferredLanguage ??
    resolveCurrentLanguage(redirectSourcePath, i18n.language, i18n.resolvedLanguage)
  const targetPath = `${toLocalizedPath(redirectSourcePath, currentLanguage)}${location.search}${location.hash}`

  return <Navigate to={targetPath} replace />
}

type AliasDetailRedirectProps = {
  language: string
  targetBasePath: string
}

const AliasDetailRedirect = ({ language, targetBasePath }: AliasDetailRedirectProps) => {
  const { id } = useParams<{ id: string }>()
  const normalizedLanguage = normalizeLanguage(language) ?? DEFAULT_LANGUAGE
  const targetPath = id
    ? toLocalizedPath(`${targetBasePath}/${id}`, normalizedLanguage)
    : toLocalizedPath(targetBasePath, normalizedLanguage)

  return <Navigate to={targetPath} replace />
}

const LocalizedLayout = ({ mode, onToggleMode }: ModeToggleProps) => {
  const { lang } = useParams<{ lang: string }>()
  const { i18n } = useTranslation()
  const location = useLocation()
  const normalizedLanguage = normalizeLanguage(lang)

  useLayoutEffect(() => {
    if (!normalizedLanguage || i18n.resolvedLanguage === normalizedLanguage) {
      return
    }

    void i18n.changeLanguage(normalizedLanguage)
  }, [i18n, normalizedLanguage])

  if (!normalizedLanguage) {
    const pathSegments = location.pathname.split('/').filter(Boolean)
    const pathWithoutInvalidLanguage =
      pathSegments.length > 1 ? `/${pathSegments.slice(1).join('/')}` : '/'

    return <LanguagePathRedirect sourcePathname={pathWithoutInvalidLanguage} />
  }

  const localizedPath = (path: string) => toLocalizedPath(path, normalizedLanguage)
  const archiveSlug = getLocalizedSegment('archive', normalizedLanguage)
  const seriesSlug = getLocalizedSegment('series', normalizedLanguage)
  const blogsSlug = getLocalizedSegment('blogs', normalizedLanguage)
  const mediaSlug = getLocalizedSegment('media', normalizedLanguage)
  const productionsSlug = getLocalizedSegment('productions', normalizedLanguage)

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar mode={mode} onToggleMode={onToggleMode} />
      <Box component="main" sx={{ flexGrow: 1 }}>
        <Routes>
          <Route index element={<HomePage />} />
          <Route path={archiveSlug} element={<ProductionsPage />} />
          <Route
            path={productionsSlug}
            element={<Navigate to={localizedPath('/archive')} replace />}
          />
          <Route path={`${productionsSlug}/:id`} element={<ProductionDetailPage />} />
          <Route path={seriesSlug} element={<SeriesPage />} />
          <Route path={`${seriesSlug}/:id`} element={<SeriesDetailPage />} />
          <Route path={blogsSlug} element={<BlogsPage />} />
          <Route path={`${blogsSlug}/:id`} element={<BlogDetailPage />} />
          <Route path={mediaSlug} element={<Navigate to={localizedPath('/archive')} replace />} />
          {/* TODO: Remove after media page is implemented */}
          <Route
            path={`${mediaSlug}/:id`}
            element={<Navigate to={localizedPath('/archive')} replace />}
          />
          {/* TODO: Remove after media page is implemented */}
          {/* Compatibility aliases from untranslated slug paths. */}
          {archiveSlug !== 'archive' && (
            <Route path="archive" element={<Navigate to={localizedPath('/archive')} replace />} />
          )}
          {archiveSlug !== 'archief' && (
            <Route path="archief" element={<Navigate to={localizedPath('/archive')} replace />} />
          )}
          {productionsSlug !== 'productions' && (
            <Route
              path="productions"
              element={<Navigate to={localizedPath('/archive')} replace />}
            />
          )}
          {productionsSlug !== 'producties' && (
            <Route
              path="producties"
              element={<Navigate to={localizedPath('/archive')} replace />}
            />
          )}
          {productionsSlug !== 'productions' && (
            <Route
              path="productions/:id"
              element={
                <AliasDetailRedirect language={normalizedLanguage} targetBasePath="/productions" />
              }
            />
          )}
          {productionsSlug !== 'producties' && (
            <Route
              path="producties/:id"
              element={
                <AliasDetailRedirect language={normalizedLanguage} targetBasePath="/productions" />
              }
            />
          )}
          {seriesSlug !== 'series' && (
            <Route path="series" element={<Navigate to={localizedPath('/series')} replace />} />
          )}
          {seriesSlug !== 'reeksen' && (
            <Route path="reeksen" element={<Navigate to={localizedPath('/series')} replace />} />
          )}
          {seriesSlug !== 'series' && (
            <Route
              path="series/:id"
              element={
                <AliasDetailRedirect language={normalizedLanguage} targetBasePath="/series" />
              }
            />
          )}
          {seriesSlug !== 'reeksen' && (
            <Route
              path="reeksen/:id"
              element={
                <AliasDetailRedirect language={normalizedLanguage} targetBasePath="/series" />
              }
            />
          )}
          {blogsSlug !== 'blogs' && (
            <Route path="blogs" element={<Navigate to={localizedPath('/blogs')} replace />} />
          )}
          {blogsSlug !== 'blogs' && <Route path="blogs/:id" element={<BlogDetailPage />} />}
          {mediaSlug !== 'media' && (
            <Route path="media" element={<Navigate to={localizedPath('/archive')} replace />} />
          )}
          {mediaSlug !== 'media' && (
            <Route path="media/:id" element={<Navigate to={localizedPath('/archive')} replace />} />
          )}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Box>
      <Footer />
    </Box>
  )
}

const Router = ({ mode, onToggleMode }: ModeToggleProps) => {
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
