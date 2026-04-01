/*
 * Displays a single production with image, metadata, description and tags.
 * Designed to be reusable across different pages (lists, search, etc.).
 */

import { Card, CardContent, Chip, Stack, Typography } from '@mui/material'

type Props = {
  title: string
  meta: string
  description: string
  tags: string[]
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
        {/* Geen row layout meer nodig */}
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
            {tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" />
            ))}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default ProductionCard
