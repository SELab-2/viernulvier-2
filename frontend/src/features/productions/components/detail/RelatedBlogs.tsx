import { Box, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import Carousel from '../../../../shared/components/Carousel'
import { tokens } from '../../../../theme/tokens'
import BlogGridCard from '../../../blogs/components/BlogGridCard'

import type { BlogCardData } from '../../../../types/Blogs'

interface RelatedBlogsProps {
  blogs: BlogCardData[]
}

function RelatedBlogs({ blogs }: RelatedBlogsProps) {
  const { t } = useTranslation()

  // Early return: no related content to render
  if (blogs.length === 0) {
    return null
  }

  return (
    <Stack
      spacing={3}
      sx={{
        p: 2,
        width: '100%',
        maxWidth: 1250,
        mx: 'auto',
      }}
    >
      {/* Section title */}
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

      {/* Horizontal carousel of blog cards */}
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

              // Ensure internal anchor/card fills full height for consistent layout
              '& > a': {
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
              },

              // Normalize nested Stack height behavior inside card
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
