import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Blog } from '../types/Blogs'
import Breadcrumbs from '../components/production/Breadcrumbs'
import ImageWithFallback from '../components/ImageWithFallback'
import Description from '../components/production/Description'
import RelatedProductions from '../components/production/RelatedProductions'
import BlogDetailPageSkeleton from './BlogDetailPageSkeleton'
import { getBlog } from '../services/blogs/Blogs'
import { getLocalizedValue } from '../utils/localization'

/**
 * Blog detail page
 *
 * - Fetches a blog entry by numeric `id` from the route parameters using `getBlog`.
 * - Renders breadcrumb, hero image, publication date and localized content.
 * - Uses components: `ImageWithFallback`, `Description` and `RelatedProductions`.
 * - If the blog has related `productions`, these are shown below the content using
 *   `RelatedProductions` with `showTag={false}` (no tag chip for blog use-case).
 */
const BlogDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const theme = useTheme()
  const { i18n, t } = useTranslation()
  const lang = i18n.language

  const [blog, setBlog] = useState<Blog | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const tRef = useRef(t)
  tRef.current = t

  /**
   * Effect: fetch blog by id when the route param changes.
   * - Validates that `id` is numeric, otherwise navigates back to home with an error.
   * - On fetch error navigates back to home and displays a floating alert.
   */
  useEffect(() => {
    if (!id) return
    setLoading(true)

    const parsed = Number(id)
    if (Number.isNaN(parsed)) {
      const errMsg = tRef.current('blogs.detail.error.invalidId', 'Invalid blog ID')
      navigate('/', {
        state: { floatingAlert: { open: true, message: errMsg, severity: 'error' } },
      })
      setError(errMsg)
      setLoading(false)
      return
    }

    const handleError = () => {
      const errMsg = tRef.current('blogs.detail.couldNotLoad', 'Could not load blog')
      navigate('/', {
        state: { floatingAlert: { open: true, message: errMsg, severity: 'error' } },
      })
      setError(errMsg)
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
      } catch {
        handleError()
      } finally {
        setLoading(false)
      }
    }

    fetchBlog()
  }, [id, navigate])

  if (loading) return <BlogDetailPageSkeleton />

  if (!blog) {
    return (
      <div style={{ padding: 40 }}>
        {error ? (
          <div>{error}</div>
        ) : (
          <div>{tRef.current('blogs.detail.notFound', 'Blog niet gevonden.')}</div>
        )}
      </div>
    )
  }

  // Localized text values: prefer language-specific record, fall back to display fields.
  const title = getLocalizedValue(blog.title, lang) || blog.display_title || t('blogs.unknown')
  const excerpt = getLocalizedValue(blog.excerpt, lang) || blog.display_excerpt || ''
  const body = getLocalizedValue(blog.body, lang) || ''
  const cover = blog.cover_image ?? null

  const published = blog.published_at
    ? new Date(blog.published_at).toLocaleDateString(i18n.language)
    : null

  return (
    <div
      className="blog-details-page"
      style={{
        backgroundColor: theme.palette.background.default,
        color: theme.palette.text.primary,
      }}
    >
      <div
        className="production-details-container"
        style={{ backgroundColor: theme.palette.background.default, gridTemplateColumns: '1fr' }}
      >
        <div
          className="production-details-left"
          style={{ backgroundColor: theme.palette.background.default }}
        >
          <Breadcrumbs
            items={[
              { label: 'Home', translationKey: 'nav.home', to: '/' },
              { label: 'Blogs', translationKey: 'blogs.title', to: '/blogs' },
              { label: blog.slug },
            ]}
          />

          <Box
            sx={{
              mt: 1,
              mb: 3,
              pb: 1.5,
              borderBottom: `1px solid ${theme.palette.divider}`,
            }}
          >
            {published ? (
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                {t('blogs.detail.publishedOn', 'Published on')}: {published}
              </Typography>
            ) : (
              <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                {t('blogs.detail.notPublished', 'Not published')}
              </Typography>
            )}
          </Box>

          <div
            className="hero-image"
            style={{
              width: '100%',
              aspectRatio: '16/7',
              backgroundColor: 'transparent',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '40px',
            }}
          >
            <ImageWithFallback
              src={cover}
              alt={title}
              sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>

          <Box sx={{ mb: 3 }}>
            <Typography
              variant="h4"
              sx={{ fontWeight: 700, color: theme.palette.text.primary, mb: 1.5 }}
            >
              {title}
            </Typography>
          </Box>

          <Description teaser={excerpt} description={body} />
        </div>
      </div>
      {blog.productions && blog.productions.length > 0 && (
        <div style={{ padding: '0 16px 32px' }}>
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
        </div>
      )}
    </div>
  )
}

export default BlogDetailPage
