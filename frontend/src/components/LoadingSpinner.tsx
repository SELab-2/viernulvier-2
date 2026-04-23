import { Box, CircularProgress, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'

type LoadingSpinnerProps = {
  size?: number
  color?: string
  label?: string
  fullScreen?: boolean
}

const LoadingSpinner = ({
  size = 36,
  color,
  label = 'Loading',
  fullScreen = false,
}: LoadingSpinnerProps) => {
  const theme = useTheme()
  const resolvedColor = color ?? theme.palette.text.primary

  return (
    <Box
      role="status"
      aria-live="polite"
      aria-label={label}
      data-testid="loading-spinner"
      sx={
        fullScreen
          ? {
              position: 'fixed',
              inset: 0,
              zIndex: theme.zIndex.modal,
              bgcolor: theme.palette.background.default,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1,
            }
          : {
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1,
            }
      }
    >
      <CircularProgress size={size} sx={{ color: resolvedColor }} />
      <Typography
        variant="body2"
        sx={{
          color: resolvedColor,
          fontSize: '0.85rem',
          opacity: 0.85,
        }}
      >
        {label}
      </Typography>
    </Box>
  )
}

export default LoadingSpinner
