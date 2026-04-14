/*
 * Displays a single production with metadata, description and tags.
 * Designed to be reusable across different pages (lists, search, etc.).
 */

import { Box, Card, CardContent, Stack, Typography } from '@mui/material'
import DOMPurify from 'dompurify'

import { tokens } from '../../theme/tokens'
import GenreAndTagChip from '../chips/GenreAndTagChip'

import type { KeyboardEvent, MouseEvent } from 'react'

type ProductionTag = {
  id: number | string
  name: string
  labels?: Record<string, string>
  onClick?: () => void
}

type Props = {
  title: string
  meta: string
  description: string
  tags: ProductionTag[]
  onClick?: (event: MouseEvent<HTMLDivElement>) => void
}

const ProductionCard = ({ title, meta, description, tags, onClick }: Props) => {
  const isInteractive = typeof onClick === 'function'

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!isInteractive) {
      return
    }

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onClick(event as unknown as MouseEvent<HTMLDivElement>)
    }
  }

  return (
    <Card
      elevation={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      sx={{
        flex: 1,
        width: '100%',
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        cursor: isInteractive ? 'pointer' : 'default',
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Stack spacing={1.25}>
          <Typography variant="h6" sx={{ fontWeight: tokens.typography.weights.bold }}>
            {title}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {meta}
          </Typography>

          <Box
            sx={{
              fontSize: '0.95rem',
              lineHeight: 1.8,
              color: 'text.secondary',
              '& img': {
                maxWidth: '100%',
                height: 'auto',
              },
              '& p': {
                m: 0,
              },
              '& p:not(:last-child)': {
                mb: 1,
              },
              '& a': {
                color: 'primary.main',
              },
            }}
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(description || ''),
            }}
          />

          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
            {tags.map((tag) => (
              <GenreAndTagChip
                key={tag.id}
                name={tag.name}
                labels={tag.labels ?? {}}
                id={tag.id}
                chipType="seriesTag"
                context="series"
              />
            ))}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default ProductionCard
