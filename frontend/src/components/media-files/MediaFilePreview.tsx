import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import { Box, Stack, Typography } from '@mui/material'
import { Document, Page, pdfjs } from 'react-pdf'

import type { MediaFile } from '../../types/MediaFiles'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

export interface MediaFilePreviewProps {
  mediaFile: MediaFile
  previewLabel: string
}

const MediaFilePreview = ({ mediaFile, previewLabel }: MediaFilePreviewProps) => {
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
        <Document
          file={mediaFile.file}
          loading={<Typography variant="body2">{previewLabel}</Typography>}
          error={<Typography variant="body2">{previewLabel}</Typography>}
          noData={<Typography variant="body2">{previewLabel}</Typography>}
        >
          <Page pageNumber={1} renderTextLayer={false} renderAnnotationLayer={false} width={240} />
        </Document>
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
