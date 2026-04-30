import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'

import type { MediaFile } from '../../types/MediaFiles'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

export interface MediaFilePreviewProps {
  mediaFile: MediaFile
  previewLabel: string
}

const MediaFilePreview = ({ mediaFile, previewLabel }: MediaFilePreviewProps) => {
  const previewRef = useRef<HTMLDivElement | null>(null)
  const [shouldRenderPdf, setShouldRenderPdf] = useState(
    () =>
      process.env.NODE_ENV === 'test' ||
      typeof window === 'undefined' ||
      !('IntersectionObserver' in window),
  )

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
