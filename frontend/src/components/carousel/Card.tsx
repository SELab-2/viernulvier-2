import { Box, Paper, Stack, Typography } from '@mui/material'
import { type ReactNode } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import ImageWithFallback from '../ImageWithFallback'

export interface CardProps {
  title: string
  subtitle?: ReactNode
  imageSrc?: string | null
  imageAlt: string
  href?: string
  children?: ReactNode
}

/**
 * Presentational media card used inside carousels and other listing layouts.
 *
 * The component deliberately contains no carousel logic; it only handles image, copy, hover state,
 * and optional linking.
 * 
 * TODO: check to use Jasper's Card component when available
 */
function Card({ title, subtitle, imageSrc, imageAlt, href, children }: CardProps) {
  return (
    <Paper
      component={href ? RouterLink : 'article'}
      {...(href ? { to: href } : {})}
      elevation={0}
      sx={(theme) => ({
        display: 'block',
        height: '100%',
        textDecoration: 'none',
        color: 'inherit',
        borderRadius: 2.5,
        overflow: 'hidden',
        border: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        boxShadow: '0 6px 20px rgba(0, 0, 0, 0.05)',
        transition: 'transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease',
        '&:hover': {
          transform: 'translateY(-3px)',
          boxShadow: '0 12px 26px rgba(0, 0, 0, 0.09)',
          borderColor: theme.palette.text.primary,
        },
        '&:focus-visible': {
          outline: `2px solid ${theme.palette.text.primary}`,
          outlineOffset: 3,
        },
      })}
    >
      <Box sx={{ overflow: 'hidden' }}>
        {/* Keep the image flush with the top edge so the card reads like a compact editorial tile. */}
        <ImageWithFallback
          src={imageSrc}
          alt={imageAlt}
          sx={{
            display: 'block',
            width: '100%',
            aspectRatio: '5 / 3',
            objectFit: 'cover',
            transition: 'transform 220ms ease',
            '&:hover': {
              transform: 'scale(1.02)',
            },
          }}
        />
      </Box>

      <Stack spacing={0.75} sx={{ p: 1.5, minWidth: 0 }}>
        {/* Titles stay on one line to preserve a stable grid rhythm. */}
        <Typography
          component="h3"
          variant="h6"
          sx={{
            fontSize: '0.95rem',
            fontWeight: 700,
            lineHeight: 1.15,
            letterSpacing: '-0.01em',
          }}
          noWrap
        >
          {title}
        </Typography>

        {subtitle ? (
          <Typography variant="body2" color="text.secondary" noWrap sx={{ fontSize: '0.82rem' }}>
            {subtitle}
          </Typography>
        ) : null}

        {children ? <Box sx={{ minWidth: 0 }}>{children}</Box> : null}
      </Stack>
    </Paper>
  )
}

export default Card