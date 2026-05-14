import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'

import ImageWithFallback from '../../../shared/components/ImageWithFallback'
import { tokens } from '../../../theme/tokens'
import { formatBlogPublishedDate } from '../../../utils/dateUtils'
import { resolveCurrentLanguage, toLocalizedPath } from '../../../utils/localizedRoutes'
import { htmlToPlainText } from '../../../utils/SanitizeHtml'
import { getTranslatedRecord } from '../../../utils/translations'

import type { Blog } from '../../../types/Blogs'

/**
 * BlogListCard
 *
 * Compact horizontal blog card used in list view.
 *
 * Features:
 * - localized routing per language
 * - translated title/excerpt support
 * - safe HTML stripping for excerpts
 * - fallback handling for missing content
 */
export interface BlogListCardProps {
  blog: Blog
}

const BlogListCard = ({ blog }: BlogListCardProps) => {
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const { language } = i18n

  /**
   * Resolve current UI language based on URL + i18n state.
   * Ensures correct localized routing for blog detail page.
   */
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )

  /**
   * Localized link to blog detail page.
   */
  const detailPath = toLocalizedPath(`/blogs/${blog.id}`, currentLanguage)

  /**
   * Blog title with fallback handling.
   */
  const title =
    getTranslatedRecord(blog.title, language, blog.display_title) ||
    t('blogs.detail.noTitleAvailable', 'No title available')

  /**
   * Clean excerpt by stripping HTML and resolving translations.
   */
  const excerpt = htmlToPlainText(getTranslatedRecord(blog.excerpt, language, blog.display_excerpt))

  /**
   * Formatted publication date (localized).
   */
  const publishedDate = formatBlogPublishedDate(blog.published_at, language)

  return (
    <Stack
      component={RouterLink}
      to={detailPath}
      direction="row"
      sx={(theme) => ({
        gap: 3,
        height: 170,
        p: 3,
        borderRadius: tokens.borderRadius.sm,
        overflow: 'hidden',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        textDecoration: 'none',
        color: 'inherit',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
          color: 'inherit',
        },
      })}
    >
      {/* Blog cover image */}
      <ImageWithFallback
        src={blog.cover_image ?? undefined}
        alt={title || t('blogs.home.coverAltFallback')}
        height="100%"
        sx={{ aspectRatio: 16 / 9, borderRadius: tokens.borderRadius.sm }}
      />

      {/* Main content column */}
      <Stack
        sx={{
          flex: 1,
          minWidth: 0,
          height: '100%',
          justifyContent: 'space-between',
          gap: 1,
          overflow: 'hidden',
        }}
      >
        {/* Title + excerpt */}
        <Stack spacing={1}>
          <Typography
            component="h2"
            variant="h6"
            color="text.primary"
            noWrap
            sx={{ fontWeight: 'bold' }}
          >
            {title}
          </Typography>

          <Typography
            variant="body2"
            component="div"
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              fontSize: 'inherit',
              color: 'text.secondary',
            }}
          >
            {excerpt || t('blogs.home.noExcerpt')}
          </Typography>
        </Stack>

        {/* Footer: published date or fallback state */}
        {publishedDate ? (
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', color: 'text.secondary' }}>
            <DateRangeOutlinedIcon fontSize="inherit" />
            <Typography variant="body2" noWrap>
              {publishedDate}
            </Typography>
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary" noWrap>
            {t('blogs.home.unpublished')}
          </Typography>
        )}
      </Stack>

      {/* Arrow indicator */}
      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default BlogListCard
