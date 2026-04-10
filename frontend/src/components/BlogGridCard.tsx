import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import { createCommonStyles } from '../theme/styles'
import { tokens } from '../theme/tokens'
import type { Blog } from '../types/Blogs'
import { formatBlogPublishedDate } from '../utils/blogs'
import { getTranslatedRecord } from '../utils/translations'
import ImageWithFallback from './ImageWithFallback'

export interface BlogGridCardProps {
  blog: Blog
}

const BlogGridCard = ({ blog }: BlogGridCardProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const { i18n, t } = useTranslation()
  const language = i18n.language

  const title = getTranslatedRecord(blog.title, language, blog.display_title)
  const excerpt = getTranslatedRecord(blog.excerpt, language, blog.display_excerpt)
  const publishedDate = formatBlogPublishedDate(blog.published_at, language)

  return (
    <Stack
      component={RouterLink}
      to={`/blogs/${blog.id}`}
      width={350}
      height="100%"
      borderRadius={tokens.card.borderRadius}
      overflow="hidden"
      sx={commonStyles.cardBase}
    >
      <ImageWithFallback
        src={blog.cover_image ?? undefined}
        alt={title || t('blogs.home.coverAltFallback')}
        sx={{ aspectRatio: 16 / 9 }}
      />

      <Stack
        flex={1}
        justifyContent="space-between"
        gap={tokens.spacing.numericSm}
        padding={tokens.spacing.numericLg}
      >
        <Stack spacing={1}>
          <Typography component="h2" variant="h6" color="text.primary" fontWeight="bold" noWrap>
            {title}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              minHeight: 60,
            }}
          >
            {excerpt || t('blogs.home.noExcerpt')}
          </Typography>
        </Stack>

        <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
          {publishedDate ? (
            <Stack direction="row" alignItems="center" spacing={1} color="text.secondary">
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
