import { Box } from '@mui/material'
import { lazy, Suspense, useLayoutEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'

import { NotificationProvider } from './contexts/NotificationContext'
import LoadingSpinner from './shared/components/LoadingSpinner'
import { ALERT_SEVERITIES } from './types/FloatingAlertConfig'
import {
  DEFAULT_LANGUAGE,
  getLocalizedSegment,
  inferLanguageFromPathname,
  normalizeLanguage,
  resolveCurrentLanguage,
  toLocalizedPath,
} from './utils/localizedRoutes'
import { createFloatingAlertState } from './utils/navigation'

import type { ModeToggleProps } from './types/Theme'

// Lazy-load UI chrome (navbar/footer) and the home page to reduce initial bundle size.
const Navbar = lazy(() => import('./shared/Navbar'))
const Footer = lazy(() => import('./shared/Footer'))
const HomePage = lazy(() => import('./pages/HomePage'))

// Lazy-load route pages to reduce initial bundle size
const BlogDetailPage = lazy(() => import('./features/blogs/pages/BlogDetailPage'))
const BlogsPage = lazy(() => import('./features/blogs/pages/BlogsPage'))
const MediaFilesPage = lazy(() => import('./features/media-files/pages/MediaFilesPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const ProductionDetailPage = lazy(() => import('./features/productions/pages/ProductionDetailPage'))
const ProductionsPage = lazy(() => import('./features/productions/pages/ProductionsPage'))
const SeriesDetailPage = lazy(() => import('./features/series/pages/SeriesDetailPage'))
const SeriesPage = lazy(() => import('./features/series/pages/SeriesPage'))

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
  const { i18n, t } = useTranslation()
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
      pathSegments.length > 1
        ? `/${pathSegments.slice(1).join('/')}`
        : pathSegments.length === 1
          ? `/${pathSegments[0]}`
          : '/'

    return <LanguagePathRedirect sourcePathname={pathWithoutInvalidLanguage} />
  }

  const localizedPath = (path: string) => toLocalizedPath(path, normalizedLanguage)
  const archiveSlug = getLocalizedSegment('archive', normalizedLanguage)
  const seriesSlug = getLocalizedSegment('series', normalizedLanguage)
  const blogsSlug = getLocalizedSegment('blogs', normalizedLanguage)
  const mediaSlug = getLocalizedSegment('media', normalizedLanguage)
  const productionsSlug = getLocalizedSegment('productions', normalizedLanguage)
  const mediaDetailAlertState = createFloatingAlertState({
    message: t('media.couldNotLoad', 'Could not load media file.'),
    severity: ALERT_SEVERITIES.error,
  })

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Suspense fallback={null}>
        <Navbar mode={mode} onToggleMode={onToggleMode} />
      </Suspense>
      <Box component="main" sx={{ flexGrow: 1 }}>
        <Suspense fallback={<LoadingSpinner fullScreen />}>
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
            <Route path={mediaSlug} element={<MediaFilesPage />} />
            <Route
              path={`${mediaSlug}/:id`}
              element={
                <Navigate to={localizedPath('/media')} replace state={mediaDetailAlertState} />
              }
            />
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
                  <AliasDetailRedirect
                    language={normalizedLanguage}
                    targetBasePath="/productions"
                  />
                }
              />
            )}
            {productionsSlug !== 'producties' && (
              <Route
                path="producties/:id"
                element={
                  <AliasDetailRedirect
                    language={normalizedLanguage}
                    targetBasePath="/productions"
                  />
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
              <Route path="media" element={<Navigate to={localizedPath('/media')} replace />} />
            )}
            {mediaSlug !== 'media' && (
              <Route
                path="media/:id"
                element={
                  <Navigate to={localizedPath('/media')} replace state={mediaDetailAlertState} />
                }
              />
            )}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </Box>
      <Suspense fallback={null}>
        <Footer />
      </Suspense>
    </Box>
  )
}

const Router = ({ mode, onToggleMode }: ModeToggleProps) => {
  const defaultRoot = toLocalizedPath('/', DEFAULT_LANGUAGE)

  return (
    <BrowserRouter>
      <NotificationProvider>
        <ScrollToTop />
        <Routes>
          <Route
            path="/:lang/*"
            element={<LocalizedLayout mode={mode} onToggleMode={onToggleMode} />}
          />
          <Route path="/" element={<Navigate to={defaultRoot} replace />} />
          <Route path="*" element={<LanguagePathRedirect />} />
        </Routes>
      </NotificationProvider>
    </BrowserRouter>
  )
}

export default Router
