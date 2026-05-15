import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'

import type { MediaFile } from '../../types/MediaFiles'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

// Threshold above which all pages are rendered (e.g. in the modal)
const MULTIPAGE_WIDTH_THRESHOLD = 600

export interface MediaFilePreviewProps {
  mediaFile: MediaFile
  previewLabel: string
  /**
   * When provided, the PDF is rendered at this fixed pixel width (modal use-case).
   * When omitted, the component measures its own container and renders at that width
   * - eliminating CSS-stretch blur on card previews.
   */
  pdfPageWidth?: number
}

const MediaFilePreview = ({ mediaFile, previewLabel, pdfPageWidth }: MediaFilePreviewProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [renderWidth, setRenderWidth] = useState<number | null>(pdfPageWidth ?? null)
  const [shouldRenderPdf, setShouldRenderPdf] = useState(
    () =>
      process.env.NODE_ENV === 'test' ||
      typeof window === 'undefined' ||
      !('IntersectionObserver' in window),
  )
  const [numPages, setNumPages] = useState<number | null>(null)

  // Lazy-render + measure real container width
  useEffect(() => {
    if (mediaFile.file_type !== 'pdf') {
      return
    }

    const node = containerRef.current
    if (!node) {
      return
    }

    // If a fixed width was supplied we only need the intersection observer
    if (pdfPageWidth !== undefined) {
      if (shouldRenderPdf) {
        return
      }

      const io = new IntersectionObserver(
        (entries) => {
          if (entries.some((e) => e.isIntersecting)) {
            setShouldRenderPdf(true)
            io.disconnect()
          }
        },
        { rootMargin: '200px' },
      )
      io.observe(node)
      return () => io.disconnect()
    }

    // No fixed width -> measure the container so the canvas renders at the
    // exact display size and is never stretched (= no blur).
    let intersecting = false
    let measured = false

    const applyWidth = () => {
      const w = node.getBoundingClientRect().width
      if (w > 0) {
        setRenderWidth(Math.round(w))
        measured = true
      }
    }

    const ro = new ResizeObserver(() => {
      applyWidth()
    })

    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          intersecting = true
          if (!measured) {
            applyWidth()
          }
          setShouldRenderPdf(true)
          io.disconnect()
        }
      },
      { rootMargin: '200px' },
    )

    ro.observe(node)
    io.observe(node)

    // In case the component is already in view on mount, we won't get an intersection event until something changes - but we can measure immediately
    if (node.getBoundingClientRect().width > 0 && !intersecting) {
      applyWidth()
    }

    return () => {
      ro.disconnect()
      io.disconnect()
    }
  }, [mediaFile.file_type, pdfPageWidth, shouldRenderPdf])

  // Image
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
          backgroundColor: (theme) => theme.palette.background.paper,
        }}
      />
    )
  }

  // PDF
  if (mediaFile.file_type === 'pdf') {
    const multiPage = renderWidth !== null && renderWidth >= MULTIPAGE_WIDTH_THRESHOLD

    return (
      <Box
        ref={containerRef}
        sx={{
          width: '100%',
          height: '100%',
          overflow: 'hidden',
          backgroundColor: (theme) => theme.palette.background.paper,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {
          shouldRenderPdf && renderWidth !== null ? (
            <Box
              sx={{
                width: '100%',
                maxHeight: '100%',
                overflowY: multiPage ? 'auto' : 'hidden',
              }}
            >
              <Document
                file={mediaFile.file}
                onLoadSuccess={(doc) => setNumPages(doc.numPages)}
                loading={null}
                error={null}
                noData={null}
              >
                {multiPage && numPages !== null ? (
                  Array.from({ length: numPages }, (_, i) => (
                    <Box key={`pdf-page-${i + 1}`} sx={{ mb: 2 }}>
                      <Page
                        pageNumber={i + 1}
                        renderTextLayer={false}
                        renderAnnotationLayer={false}
                        width={renderWidth}
                        loading={null}
                      />
                    </Box>
                  ))
                ) : (
                  <Page
                    pageNumber={1}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                    width={renderWidth}
                    loading={null}
                  />
                )}
              </Document>
            </Box>
          ) : null // When the PDF isn't rendered yet (lazy), don't display the filename
        }
      </Box>
    )
  }

  // Other / document
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
