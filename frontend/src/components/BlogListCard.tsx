import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link as RouterLink } from 'react-router-dom'
import { tokens } from '../theme/tokens'
import type { Blog } from '../types/Blogs'
import { formatBlogPublishedDate } from '../utils/blogs'
import { getTranslatedRecord } from '../utils/translations'
import ImageWithFallback from './ImageWithFallback'

export interface BlogListCardProps {
  blog: Blog
}

const BlogListCard = ({ blog }: BlogListCardProps) => {
  const { i18n, t } = useTranslation()
  const language = i18n.language

  const title = getTranslatedRecord(blog.title, language, blog.display_title)
  const excerpt = getTranslatedRecord(blog.excerpt, language, blog.display_excerpt)
  const publishedDate = formatBlogPublishedDate(blog.published_at, language)

  return (
    <Stack
      component={RouterLink}
      to={`/blogs/${blog.id}`}
      direction="row"
      gap={3}
      height={170}
      padding={3}
      borderRadius={tokens.borderRadius.sm}
      overflow="hidden"
      sx={(theme) => ({
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        textDecoration: 'none',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <ImageWithFallback
        src={blog.cover_image ?? undefined}
        alt={title || t('blogs.home.coverAltFallback')}
        height="100%"
        borderRadius={tokens.borderRadius.sm}
        sx={{ aspectRatio: 16 / 9 }}
      />

      <Stack
        flex={1}
        minWidth={0}
        height="100%"
        justifyContent="space-between"
        gap={1}
        overflow="hidden"
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
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {excerpt || t('blogs.home.noExcerpt')}
          </Typography>
        </Stack>

        {publishedDate ? (
          <Stack direction="row" alignItems="center" spacing={1} color="text.secondary">
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

      <Box alignSelf="center" paddingRight={2}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default BlogListCard
