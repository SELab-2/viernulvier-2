import { Box, type BoxProps } from '@mui/material'
import { useState } from 'react'

import { DarkMode } from '../../types/Theme'

export type ImageWithFallbackProps = Omit<BoxProps<'img'>, 'component' | 'src' | 'alt'> & {
  src?: string | null
  alt: string
}

/**
 * Renders a remote image when available, otherwise shows a branded fallback.
 * @param props Image source, alt text, style overrides, and remaining image props.
 */
const ImageWithFallback = (props: ImageWithFallbackProps) => {
  const { src, alt, sx, onError, ...imgProps } = props
  const [hasError, setHasError] = useState(false)
  const showImage = Boolean(src) && !hasError

  if (showImage) {
    return (
      <Box
        component="img"
        src={src!}
        alt={alt}
        loading={imgProps.loading ?? 'lazy'}
        onError={(event) => {
          setHasError(true)
          onError?.(event)
        }}
        sx={{
          display: 'block',
          objectFit: 'cover',
          backgroundColor: 'action.hover',
          ...sx,
        }}
        {...imgProps}
      />
    )
  }

  return (
    <Box
      role="img"
      aria-label={alt}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'action.hover',
        overflow: 'hidden',
        ...sx,
      }}
    >
      <Box
        component="img"
        src="/vnv_logo.png"
        alt="Fallback image"
        aria-hidden="true"
        sx={(theme) => ({
          width: 'auto',
          maxWidth: '42%',
          maxHeight: '42%',
          objectFit: 'contain',
          filter: theme.palette.mode === DarkMode ? 'brightness(0) invert(1)' : undefined,
          opacity: 0.55,
        })}
      />
    </Box>
  )
}

export default ImageWithFallback
