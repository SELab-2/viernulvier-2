import { Box, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, useParams, useNavigate } from 'react-router-dom'

import BlogDetailPageSkeleton from './BlogDetailPageSkeleton'
import ImageWithFallback from '../../../shared/components/ImageWithFallback'
import Breadcrumbs from '../../productions/components/detail/Breadcrumbs'
import Description from '../../productions/components/detail/Description'
import RelatedProductions from '../../productions/components/detail/RelatedProductions'
import { getBlog } from '../../../services/blogs/Blogs'
import { tokens } from '../../../theme/tokens'
import type { Blog } from '../../../types/Blogs'
import { formatBlogPublishedDate } from '../../../utils/dateUtils'
import { getLocalizedValue } from '../../../utils/localization'
import { resolveCurrentLanguage, toLocalizedPath } from '../../../utils/localizedRoutes'
import { ApiError } from '../../../services/ApiTypes'
import { ALERT_SEVERITIES } from '../../../types/FloatingAlertConfig'
import { redirectWithFloatingAlert } from '../../../utils/navigation'

/**
 * Blog detail page
 *
 * - Fetches a blog entry by numeric `id` from the route parameters using `getBlog`.
 * - Renders breadcrumb, hero image, publication date and localized content.
 * - Uses components: `ImageWithFallback`, `Description` and `RelatedProductions`.
 * - If the blog has related `productions`, these are shown below the content using
 *   `RelatedProductions` with `showTag={false}` (no tag chip for blog use-case).
 */
type BlogDetailContentProps = {
  id: string
}

const BlogDetailContent = ({ id }: BlogDetailContentProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { i18n, t } = useTranslation()
  const lang = i18n.language
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const blogsPath = toLocalizedPath('/blogs', currentLanguage)
  const currentPath = location.pathname

  const [blog, setBlog] = useState<Blog | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  /**
   * Effect: fetch blog by id when the route param changes.
   * - Validates that `id` is numeric, otherwise navigates back to the blogs listing with an error.
   * - On fetch error navigates back to the blogs listing and displays a floating alert.
   */
  useEffect(() => {
    const parsed = Number(id)
    if (Number.isNaN(parsed)) {
      const errMsg = t('blog.invalidId', 'Invalid blog ID')
      redirectWithFloatingAlert(navigate, blogsPath, {
        message: errMsg,
        severity: ALERT_SEVERITIES.error,
      })
      return
    }

    const handleError = (error?: unknown) => {
      // If the failure is a rate-limit, show a warning and return to the listing.
      if (error instanceof ApiError && error.status === 429) {
        redirectWithFloatingAlert(navigate, currentPath, {
          message: error.message,
          severity: ALERT_SEVERITIES.warning,
        })
        return
      }

      // For other failures, redirect to the site-wide localized 404 page.
      const errMsg = t('blog.couldNotLoad', 'Could not load blog')
      redirectWithFloatingAlert(navigate, toLocalizedPath('/404', currentLanguage), {
        message: errMsg,
        severity: ALERT_SEVERITIES.error,
      })
    }

    const fetchBlog = async () => {
      try {
        const data = await getBlog(parsed)

        // If the blog exists but is not yet published, handle like a load error:
        // navigate to the blogs listing and show a floating error alert.
        if (!data.published_at) {
          handleError()
          return
        }
        setBlog(data)
      } catch (error: unknown) {
        handleError(error)
      } finally {
        setLoading(false)
      }
    }

    fetchBlog()
  }, [blogsPath, currentLanguage, id, navigate, t, currentPath])

  if (loading) {
    return <BlogDetailPageSkeleton />
  }

  if (!blog) {
    return null
  }

  // Localized text values: prefer language-specific record, fall back to display fields.
  const title =
    getLocalizedValue(blog.title, lang) ||
    blog.display_title ||
    t('blogs.detail.noTitleAvailable', 'No title available')
  const excerpt = getLocalizedValue(blog.excerpt, lang) || blog.display_excerpt || ''
  const body = getLocalizedValue(blog.body, lang) || ''
  const cover = blog.cover_image ?? null

  const published = formatBlogPublishedDate(blog.published_at, i18n.language)

  return (
    <Box
      className="blog-details-page"
      sx={(theme) => ({
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      })}
    >
      <Box
        className="production-details-container"
        sx={(theme) => ({
          display: 'grid',
          gridTemplateColumns: '1fr',
          backgroundColor: theme.palette.background.default,
        })}
      >
        <Box
          className="production-details-left"
          sx={(theme) => ({ backgroundColor: theme.palette.background.default })}
        >
          <Breadcrumbs
            items={[
              { label: 'Home', translationKey: 'nav.home', to: '/' },
              { label: 'Blogs', translationKey: 'blogs.title', to: '/blogs' },
              { label: blog.slug },
            ]}
          />

          <Box
            sx={(theme) => ({
              mt: 1,
              mb: 3,
              pb: 1.5,
              borderBottom: `1px solid ${theme.palette.divider}`,
            })}
          >
            {published ? (
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {t('blogs.detail.publishedOn', 'Published on')}: {published}
              </Typography>
            ) : (
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {t('blogs.detail.notPublished', 'Not published')}
              </Typography>
            )}
          </Box>

          <Box
            className="hero-image"
            sx={{
              width: '100%',
              aspectRatio: '16 / 7',
              backgroundColor: 'transparent',
              borderRadius: tokens.borderRadius.sm,
              overflow: 'hidden',
              mb: 5,
            }}
          >
            <ImageWithFallback
              src={cover}
              alt={title}
              sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography
              variant="h4"
              sx={{ fontWeight: tokens.typography.weights.bold, color: 'text.primary', mb: 1.5 }}
            >
              {title}
            </Typography>
          </Box>

          <Description teaser={excerpt} description={body} />
        </Box>
      </Box>
      {blog.productions && blog.productions.length > 0 && (
        <Box sx={{ px: 2, pb: 4 }}>
          <RelatedProductions
            related={[
              {
                tag: {
                  id: 0,
                  name: {},
                  display_name: t('blogs.detail.related', 'Related productions'),
                },
                productions: blog.productions,
              },
            ]}
            lang={lang}
            showTag={false}
          />
        </Box>
      )}
    </Box>
  )
}

const BlogDetailPage = () => {
  const { id } = useParams()

  if (!id) {
    return null
  }

  return <BlogDetailContent key={id} id={id} />
}

export default BlogDetailPage
