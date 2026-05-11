import { Box, type BoxProps } from '@mui/material'
import { useState } from 'react'

import { DarkMode } from '../../types/Theme'

export type ImageWithFallbackProps = Omit<BoxProps<'img'>, 'component' | 'src' | 'alt'> & {
  src?: string | null
  alt: string
}

/**
 * Image with a remote `src`, or a centered branded logo on a neutral background when the URL is
 * missing or the request fails.
 *
 * @param props {@link ImageWithFallbackProps}: optional `src` (falsy shows fallback), required
 *   `alt`, optional `sx`, `onError`, and remaining Box-as-`img` props for the loaded image only.
 * @returns The image or fallback subtree.
 */
const ImageWithFallback = ({ src, alt, sx, onError, ...props }: ImageWithFallbackProps) => {
  const [hasError, setHasError] = useState(false)
  const showImage = Boolean(src) && !hasError

  if (showImage) {
    return (
      <Box
        component="img"
        src={src!}
        alt={alt}
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
        {...props}
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
