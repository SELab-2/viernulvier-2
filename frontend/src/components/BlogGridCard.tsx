import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink, useLocation } from 'react-router-dom'

import HtmlText from './HtmlText'
import ImageWithFallback from './ImageWithFallback'
import { createCommonStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import { formatBlogPublishedDate } from '../utils/blogs'
import { resolveCurrentLanguage, toLocalizedPath } from '../utils/localizedRoutes'
import { sanitizeHtml, forbidImagesRule, forbidEmbedsRule } from '../utils/SanitizeHtml'
import { getTranslatedRecord } from '../utils/translations'

import type { Blog } from '../types/Blogs'

export interface BlogGridCardProps {
  blog: Blog
}

const BlogGridCard = ({ blog }: BlogGridCardProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const { i18n, t } = useTranslation()
  const location = useLocation()
  const { language } = i18n
  const currentLanguage = resolveCurrentLanguage(
    location.pathname,
    i18n.language,
    i18n.resolvedLanguage,
  )
  const detailPath = toLocalizedPath(`/blogs/${blog.id}`, currentLanguage)

  const title =
    getTranslatedRecord(blog.title, language, blog.display_title) ||
    t('blogs.detail.noTitleAvailable', 'No title available')
  const excerpt = getTranslatedRecord(blog.excerpt, language, blog.display_excerpt)
  const publishedDate = formatBlogPublishedDate(blog.published_at, language)

  return (
    <Stack
      component={RouterLink}
      to={detailPath}
      sx={{
        ...commonStyles.cardBase,
        width: '100%',
        maxWidth: tokens.card.gridCardWidthPx,
        height: '100%',
        borderRadius: tokens.card.borderRadius,
        overflow: 'hidden',
        textDecoration: 'none',
        color: 'inherit',
        '&:hover': {
          textDecoration: 'none',
        },
      }}
    >
      <ImageWithFallback
        src={blog.cover_image ?? undefined}
        alt={title || t('blogs.home.coverAltFallback')}
        sx={{ aspectRatio: 16 / 9 }}
      />

      <Stack
        sx={{
          flex: 1,
          justifyContent: 'space-between',
          gap: tokens.spacing.numericSm,
          p: tokens.spacing.numericLg,
        }}
      >
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
          <HtmlText
            html={sanitizeHtml(excerpt, [forbidImagesRule, forbidEmbedsRule])}
            variant="body2"
            component="div"
            fallback={t('blogs.home.noExcerpt')}
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              minHeight: 60,
              fontSize: 'inherit',
              color: 'text.secondary',
            }}
          />
        </Stack>

        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: 'center', justifyContent: 'space-between' }}
        >
          {publishedDate ? (
            <Stack
              direction="row"
              spacing={1}
              sx={{ alignItems: 'center', color: 'text.secondary' }}
            >
              <DateRangeOutlinedIcon fontSize="inherit" />
              <Typography variant="body2">{publishedDate}</Typography>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t('blogs.home.unpublished')}
            </Typography>
          )}
        </Stack>
      </Stack>
    </Stack>
  )
}

export default BlogGridCard
