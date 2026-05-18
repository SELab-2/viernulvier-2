import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography, Box } from '@mui/material'
import { useTranslation } from 'react-i18next'

import MediaFilePreview from './MediaFilePreview'
import {
  formatMediaFileDate,
  formatMediaFileSize,
  getMediaFileDescription,
  getMediaFileTypeLabel,
} from './MediaFileUtils'
import { tokens } from '../../../theme/tokens'
import { getPublicMediaFileUrl } from '../../../utils/mediaFileUrls'

import type { MediaFile } from '../../../types/MediaFiles'

/**
 * Props for MediaFileListCard component.
 */
export interface MediaFileListCardProps {
  mediaFile: MediaFile
  onOpen?: (mediaFile: MediaFile) => void
}

/**
 * Renders a media file in list layout (row-based card).
 *
 * Layout:
 * - Left: preview (image/pdf/icon)
 * - Right: metadata (filename, description, date, size)
 *
 * Clicking the card opens the public file URL.
 */
const MediaFileListCard = ({ mediaFile, onOpen }: MediaFileListCardProps) => {
  const { t, i18n } = useTranslation()
  const { language } = i18n

  /**
   * Derived metadata for display.
   */
  const uploadedAt = formatMediaFileDate(mediaFile.created_at, language)
  const fileSize = formatMediaFileSize(mediaFile.size_bytes)
  const description = getMediaFileDescription(mediaFile, i18n.language, t)
  const fileTypeLabel = getMediaFileTypeLabel(mediaFile, t)
  const fileUrl = getPublicMediaFileUrl(mediaFile.file)

  return (
    <Stack
      component="a"
      href={fileUrl}
      direction="row"
      onClick={(event) => {
        if (!onOpen) {
          return
        }

        event.preventDefault()
        onOpen(mediaFile)
      }}
      aria-label={mediaFile.filename}
      sx={(theme) => ({
        gap: 3,
        height: 170,
        p: 3,
        width: '100%',
        minWidth: 0,
        borderRadius: tokens.borderRadius.sm,
        overflow: 'hidden',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        textDecoration: 'none',
        color: 'inherit',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
          color: 'inherit',
          textDecoration: 'none',
        },
      })}
    >
      {/* LEFT: preview container */}
      <Stack
        sx={{
          aspectRatio: '16 / 9',
          height: '100%',
          flexShrink: 0,
          borderRadius: tokens.borderRadius.sm,
          overflow: 'hidden',
          backgroundColor: 'action.hover',
        }}
      >
        <MediaFilePreview mediaFile={mediaFile} previewLabel={fileTypeLabel} />
      </Stack>

      {/* RIGHT: metadata content */}
      <Stack
        sx={{
          flex: 1,
          minWidth: 0,
          height: '100%',
          justifyContent: 'space-between',
          gap: 1,
          overflow: 'hidden',
        }}
      >
        {/* Filename + description */}
        <Stack spacing={1}>
          <Typography
            component="h2"
            variant="h6"
            color="text.primary"
            sx={{
              fontWeight: 'bold',
              overflowWrap: 'anywhere',
              wordBreak: 'break-word',
            }}
          >
            {mediaFile.filename}
          </Typography>

          <Typography
            variant="body2"
            component="div"
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              minHeight: 60,
              fontSize: 'inherit',
              color: 'text.secondary',
            }}
          >
            {description || fileTypeLabel}
          </Typography>
        </Stack>

        {/* Footer metadata row */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1}
          sx={{
            alignItems: { xs: 'flex-start', sm: 'center' },
            justifyContent: { sm: 'space-between' },
            color: 'text.secondary',
            minWidth: 0,
          }}
        >
          {/* upload date */}
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
            <DateRangeOutlinedIcon fontSize="inherit" />
            <Typography variant="body2" noWrap>
              {uploadedAt}
            </Typography>
          </Stack>

          {/* file size (optional) */}
          {fileSize ? (
            <Typography variant="body2" noWrap>
              {t('media.size')}: {fileSize}
            </Typography>
          ) : null}
        </Stack>
      </Stack>
      {/* Arrow indicator */}
      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default MediaFileListCard
