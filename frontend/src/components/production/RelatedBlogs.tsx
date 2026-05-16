import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import { tokens } from '../../theme/tokens'
import BlogGridCard from '../BlogGridCard'
import Carousel from '../carousel/Carousel'

import type { BlogCardData } from '../../types/Blogs'

interface RelatedBlogsProps {
  blogs: BlogCardData[]
}

function RelatedBlogs({ blogs }: RelatedBlogsProps) {
  const { t } = useTranslation()

  if (blogs.length === 0) {
    return null
  }

  return (
    <Stack spacing={3} sx={{ p: 2, width: '100%', maxWidth: 1250, mx: 'auto' }}>
      <Typography
        variant="h5"
        sx={(theme) => ({
          fontWeight: tokens.typography.weights.bold,
          fontSize: { xs: '1.05rem', sm: '1.25rem' },
          letterSpacing: '-0.01em',
          color: theme.palette.text.primary,
        })}
      >
        {t('productions.detail.relatedBlogs', 'Related blogs')}
      </Typography>
      <Carousel
        ariaLabel={t('productions.detail.relatedBlogs', 'Related blogs')}
        maxWidth="100%"
        previousLabel={t('carousel.previousSlide', 'Previous slide')}
        nextLabel={t('carousel.nextSlide', 'Next slide')}
        slideLabel={t('carousel.goToSlide', 'Go to slide')}
        sx={{ width: '100%' }}
      >
        {blogs.map((blog) => (
          <Box
            key={blog.id}
            sx={{
              width: { xs: 'calc(100vw - 80px)', sm: tokens.card.gridCardWidthPx },
              maxWidth: 'calc(100vw - 80px)',
              display: 'flex',
              alignItems: 'stretch',
              '& > a': {
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
              },
              '& > a > .MuiStack-root': {
                height: '100%',
              },
            }}
          >
            <BlogGridCard blog={blog} />
          </Box>
        ))}
      </Carousel>
    </Stack>
  )
}

export default RelatedBlogs
