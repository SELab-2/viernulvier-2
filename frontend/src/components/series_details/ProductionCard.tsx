/*
 * Displays a single production with image, metadata, description and tags.
 * Designed to be reusable across different pages (lists, search, etc.).
 */

import { Avatar, Card, CardContent, Chip, Stack, Typography } from '@mui/material'

type Props = {
  title: string
  meta: string
  description: string
  tags: string[]
  image: string
}

const ProductionCard = ({ title, meta, description, tags, image }: Props) => {
  return (
    <Card
      elevation={0}
      sx={{
        // Full-width flexible card with subtle border
        flex: 1,
        width: '100%',
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2.5}>
          {/* Preview image */}
          <Avatar
            variant="rounded"
            src={image}
            alt={title}
            sx={{
              width: { xs: '100%', sm: 140 },
              height: { xs: 180, sm: 105 },
              borderRadius: 2,
              flexShrink: 0, // Prevent shrinking in flex layout
            }}
          />

          {/* Text content */}
          <Stack spacing={1.25} sx={{ flex: 1, minWidth: 0 }}>
            {/* Title */}
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {title}
            </Typography>

            {/* Metadata (date, location, etc.) */}
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
        </Stack>
      </CardContent>
    </Card>
  )
}

export default ProductionCard
