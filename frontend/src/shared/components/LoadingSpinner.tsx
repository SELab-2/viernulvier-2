import { Box, CircularProgress, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'

type LoadingSpinnerProps = {
  /**
   * Size of the circular progress indicator in pixels.
   * @default 36
   */
  size?: number

  /**
   * Optional custom color for spinner and text.
   * If not provided, theme text color is used.
   */
  color?: string

  /**
   * Accessible label and visible text under the spinner.
   * @default "Loading"
   */
  label?: string

  /**
   * If true, renders as a full-screen overlay centered loader.
   * Useful for page-level loading states.
   * @default false
   */
  fullScreen?: boolean
}

/**
 * LoadingSpinner
 *
 * A reusable loading indicator component built on top of MUI's CircularProgress.
 *
 * Features:
 * - Centered layout with optional full-screen overlay mode
 * - Accessible via role="status" and aria-live="polite"
 * - Themed coloring with optional override
 * - Optional label for UX clarity
 *
 * @param size - Diameter of spinner in pixels
 * @param color - Optional override color for spinner and label
 * @param label - Text displayed below spinner and used for accessibility
 * @param fullScreen - Whether to render as fullscreen overlay
 */
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
