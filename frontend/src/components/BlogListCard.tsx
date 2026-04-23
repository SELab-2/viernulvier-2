import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'

import HtmlText from './HtmlText'
import ImageWithFallback from './ImageWithFallback'
import { tokens } from '../theme/tokens'
import { formatBlogPublishedDate } from '../utils/blogs'
import { getTranslatedRecord } from '../utils/translations'

import type { Blog } from '../types/Blogs'

export interface BlogListCardProps {
  blog: Blog
}

const BlogListCard = ({ blog }: BlogListCardProps) => {
  const { i18n, t } = useTranslation()
  const { language } = i18n

  const title =
    getTranslatedRecord(blog.title, language, blog.display_title) ||
    t('blogs.detail.noTitleAvailable', 'No title available')
  const excerpt = getTranslatedRecord(blog.excerpt, language, blog.display_excerpt)
  const publishedDate = formatBlogPublishedDate(blog.published_at, language)

  return (
    <Stack
      component={RouterLink}
      to={`/blogs/${blog.id}`}
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
      <ImageWithFallback
        src={blog.cover_image ?? undefined}
        alt={title || t('blogs.home.coverAltFallback')}
        height="100%"
        sx={{ aspectRatio: 16 / 9, borderRadius: tokens.borderRadius.sm }}
      />

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
            html={excerpt}
            variant="body2"
            component="div"
            fallback={t('blogs.home.noExcerpt')}
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              fontSize: 'inherit',
              color: 'text.secondary',
            }}
          />
        </Stack>

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

      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default BlogListCard
