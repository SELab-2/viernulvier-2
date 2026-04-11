/*
 * Displays a single production with metadata, description and tags.
 * Designed to be reusable across different pages (lists, search, etc.).
 */

import { Card, CardContent, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import type { Tag } from '../../types/Tags'
import GenreAndTagChip from '../chips/GenreAndTagChip'
import { getTranslatedRecord } from '../../utils/translations'

type Props = {
  title: string
  meta: string
  description: string
  tags: Tag[]
}

const ProductionCard = ({ title, meta, description, tags }: Props) => {
  const { i18n } = useTranslation()

  return (
    <Card
      elevation={0}
      sx={{
        flex: 1,
        width: '100%',
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Stack spacing={1.25}>
          {/* Title */}
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>

          {/* Metadata */}
          <Typography variant="body2" color="text.secondary">
            {meta}
          </Typography>

          {/* Description */}
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>

          {/* Tags */}
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {tags.map((tag) => {
              const tagLabel = getTranslatedRecord(tag.name, i18n.language, tag.display_name || '')
              return (
                <GenreAndTagChip
                  key={tag.id}
                  name={tagLabel}
                  labels={tag.name || {}}
                  id={tag.id}
                  chipType="seriesTag"
                  context="series"
                />
              )
            })}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default ProductionCard
