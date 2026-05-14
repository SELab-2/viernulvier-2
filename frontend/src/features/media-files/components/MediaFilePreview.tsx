import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'

import type { MediaFile } from '../../../types/MediaFiles'

/**
 * Configures the PDF.js worker so that react-pdf can render PDFs correctly.
 * Uses a CDN-based worker matching the installed pdfjs version.
 */
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

/**
 * Props for MediaFilePreview component.
 */
export interface MediaFilePreviewProps {
  mediaFile: MediaFile
  previewLabel: string
}

/**
 * Renders a preview for different media file types (image, PDF, or fallback icon).
 *
 * - Images are rendered directly via <img>
 * - PDFs are lazily rendered using IntersectionObserver + react-pdf
 * - Other file types show a generic icon + label
 */
const MediaFilePreview = ({ mediaFile, previewLabel }: MediaFilePreviewProps) => {
  const previewRef = useRef<HTMLDivElement | null>(null)

  /**
   * Controls whether the PDF renderer should be mounted.
   * Initially disabled and only enabled when:
   * - component is in viewport (lazy load), OR
   * - SSR/test environments, OR
   * - IntersectionObserver is unavailable
   */
  const [shouldRenderPdf, setShouldRenderPdf] = useState(
    () =>
      process.env.NODE_ENV === 'test' ||
      typeof window === 'undefined' ||
      !('IntersectionObserver' in window),
  )

  /**
   * Sets up an IntersectionObserver to lazily load PDF rendering
   * when the preview container comes into view.
   */
  useEffect(() => {
    if (mediaFile.file_type !== 'pdf' || shouldRenderPdf) {
      return
    }

    const node = previewRef.current
    if (!node) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setShouldRenderPdf(true)
          observer.disconnect()
        }
      },
      { rootMargin: '200px' },
    )

    observer.observe(node)

    return () => {
      observer.disconnect()
    }
  }, [mediaFile.file_type, shouldRenderPdf])

  /**
   * IMAGE PREVIEW
   * Direct rendering for image-type media files.
   */
  if (mediaFile.file_type === 'image') {
    return (
      <Box
        component="img"
        src={mediaFile.file}
        alt={mediaFile.filename}
        sx={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: 'block',
          backgroundColor: 'grey.100',
        }}
      />
    )
  }

  /**
   * PDF PREVIEW
   * Uses react-pdf with lazy loading and fallback label while loading/error.
   */
  if (mediaFile.file_type === 'pdf') {
    return (
      <Box
        ref={previewRef}
        sx={{
          width: '100%',
          height: '100%',
          overflow: 'hidden',
          backgroundColor: 'grey.100',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          '& canvas': {
            width: '100% !important',
            height: '100% !important',
            objectFit: 'cover',
            display: 'block',
          },
        }}
      >
        {shouldRenderPdf ? (
          <Document
            file={mediaFile.file}
            loading={<Typography variant="body2">{previewLabel}</Typography>}
            error={<Typography variant="body2">{previewLabel}</Typography>}
            noData={<Typography variant="body2">{previewLabel}</Typography>}
          >
            <Page
              pageNumber={1}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              width={240}
            />
          </Document>
        ) : (
          <Typography variant="body2">{previewLabel}</Typography>
        )}
      </Box>
    )
  }

  /**
   * FALLBACK PREVIEW
   * Used for unsupported or generic file types.
   */
  return (
    <Stack
      spacing={1}
      sx={{
        width: '100%',
        height: '100%',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'text.secondary',
        backgroundColor: 'action.hover',
      }}
    >
      {mediaFile.file_type === 'other' ? (
        <InsertDriveFileOutlinedIcon sx={{ fontSize: 54 }} />
      ) : (
        <DescriptionOutlinedIcon sx={{ fontSize: 54 }} />
      )}
      <Typography variant="body2">{previewLabel}</Typography>
    </Stack>
  )
}

export default MediaFilePreview
