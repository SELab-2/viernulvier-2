import { Box, Chip, Stack, Typography } from '@mui/material'

type Props = {
  name: string
  description: string
  badge: string
}

const SeriesHeader = ({ name, description, badge }: Props) => {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={3}>
      <Box
        sx={{
          maxWidth: 760,
          width: '100%',
          minWidth: 0,
        }}
      >
        <Typography
          variant="h3"
          sx={{
            fontWeight: 800,
            mb: 2,
            fontSize: { xs: '2.5rem', sm: '3rem', md: '3.75rem' },
            overflowWrap: 'break-word',
          }}
        >
          {name}
        </Typography>

        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '1rem', md: '1.05rem' },
            overflowWrap: 'break-word',
          }}
        >
          {description}
        </Typography>
      </Box>

      <Chip
        label={badge}
        color="secondary"
        sx={{
          borderRadius: 999,
          px: 1,
          fontWeight: 600,
          maxWidth: '100%',
          '& .MuiChip-label': { whiteSpace: 'normal' },
        }}
      />
    </Stack>
  )
}

export default SeriesHeader
