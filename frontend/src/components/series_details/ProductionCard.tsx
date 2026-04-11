/*
 * Displays a single production with metadata, description and tags.
 * Designed to be reusable across different pages (lists, search, etc.).
 */

import { Card, CardContent, Stack, Typography } from '@mui/material'
import GenreAndTagChip from '../chips/GenreAndTagChip'
import { getTranslatedRecord } from '../../utils/translations'
import type { Tag } from '../../types/Tags'

type Props = {
  title: string
  meta: string
  description: string
  tags: Tag[]
  lang?: string
}

const ProductionCard = ({ title, meta, description, tags, lang = 'nl' }: Props) => {
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

          <Stack direction="row" spacing={1} flexWrap="wrap">
            {tags.map((tag) => (
              <GenreAndTagChip
                key={tag.id}
                name={getTranslatedRecord(tag.name, lang, tag.display_name ?? String(tag.id))}
                labels={{}}
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
