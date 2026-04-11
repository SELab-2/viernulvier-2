/*
 * Displays a single production with metadata, description and tags.
 * Designed to be reusable across different pages (lists, search, etc.).
 */

import { Card, CardContent, Stack, Typography } from '@mui/material'
import GenreAndTagChip from '../chips/GenreAndTagChip'

type ProductionTag = {
  id: number | string
  name: string
  labels?: Record<string, string>
}

type Props = {
  title: string
  meta: string
  description: string
  tags: ProductionTag[]
}

const ProductionCard = ({ title, meta, description, tags }: Props) => {
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
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {meta}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>

          <Stack direction="row" spacing={1} flexWrap="wrap">
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
