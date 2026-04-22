import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import PictureAsPdfOutlinedIcon from '@mui/icons-material/PictureAsPdfOutlined'
import { Box, Stack, Typography } from '@mui/material'

import type { MediaFile } from '../../types/MediaFiles'

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
      {mediaFile.file_type === 'pdf' ? (
        <PictureAsPdfOutlinedIcon sx={{ fontSize: 54 }} />
      ) : mediaFile.file_type === 'other' ? (
        <InsertDriveFileOutlinedIcon sx={{ fontSize: 54 }} />
      ) : (
        <DescriptionOutlinedIcon sx={{ fontSize: 54 }} />
      )}
      <Typography variant="body2">{previewLabel}</Typography>
    </Stack>
  )
}

export default MediaFilePreview
