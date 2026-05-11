/*
 * Displays the main header of a series detail page: title and description.
 */

import { Stack, Typography } from '@mui/material'

import HtmlText from '../../../shared/components/HtmlText'

type Props = {
  name: string
  excerpt?: string
  description: string
}

const SeriesHeader = ({ name, excerpt, description }: Props) => {
  return (
    <Stack spacing={2} sx={{ maxWidth: 760 }}>
      <Typography variant="h3" sx={{ fontWeight: 800, overflowWrap: 'break-word' }}>
        {name}
      </Typography>
      {excerpt ? (
        <HtmlText
          html={excerpt}
          variant="body1"
          component="div"
          sx={{
            color: 'text.secondary',
            overflowWrap: 'break-word',
            fontSize: 'inherit',
            fontStyle: 'italic',
          }}
        />
      ) : null}
      <HtmlText
        html={description}
        variant="body1"
        component="div"
        sx={{
          color: 'text.secondary',
          overflowWrap: 'break-word',
          fontSize: 'inherit',
        }}
      />
    </Stack>
  )
}

export default SeriesHeader
