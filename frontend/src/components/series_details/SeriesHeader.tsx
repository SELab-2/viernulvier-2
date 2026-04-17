/*
 * Displays the main header of a series detail page: title and description.
 */

import { Stack, Typography } from '@mui/material'

type Props = {
  name: string
  description: string
}

const SeriesHeader = ({ name, description }: Props) => {
  return (
    <Stack spacing={2} sx={{ maxWidth: 760 }}>
      <Typography variant="h3" sx={{ fontWeight: 800, overflowWrap: 'break-word' }}>
        {name}
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ overflowWrap: 'break-word' }}>
        {description}
      </Typography>
    </Stack>
  )
}

export default SeriesHeader
