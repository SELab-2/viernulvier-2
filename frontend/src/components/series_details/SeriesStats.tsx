import { Box, Divider, Stack, Typography } from '@mui/material'

type Stat = {
  value: string
  label: string
}

type Props = {
  stats: Stat[]
}

const SeriesStats = ({ stats }: Props) => {
  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      spacing={{ xs: 2, sm: 5 }}
      divider={
        <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
      }
      sx={{ py: 1 }}
    >
      {stats.map((stat) => (
        <Box key={stat.value + stat.label}>
          <Typography variant="h4" sx={{ fontWeight: 800 }}>
            {stat.value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {stat.label}
          </Typography>
        </Box>
      ))}
    </Stack>
  )
}

export default SeriesStats
