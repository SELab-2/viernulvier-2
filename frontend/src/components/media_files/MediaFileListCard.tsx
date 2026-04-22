import ArrowForwardOutlinedIcon from '@mui/icons-material/ArrowForwardOutlined'
import { Box, Chip, Stack, Tooltip, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import MediaFilePreview from './MediaFilePreview'
import {
  formatMediaFileDate,
  formatMediaFileSize,
  getMediaFileDescription,
  getMediaFileTypeLabel,
} from './MediaFileUtils'

import type { MediaFile } from '../../types/MediaFiles'

export interface MediaFileListCardProps {
  mediaFile: MediaFile
}

const MediaFileListCard = ({ mediaFile }: MediaFileListCardProps) => {
  const { i18n, t } = useTranslation()
  const locale = i18n.language

  const uploadedAt = formatMediaFileDate(mediaFile.created_at, locale)
  const fileSize = formatMediaFileSize(mediaFile.size_bytes)
  const description = getMediaFileDescription(mediaFile, locale)
  const fileTypeLabel = getMediaFileTypeLabel(mediaFile, t)

  return (
    <Stack
      component="a"
      href={mediaFile.file}
      target="_blank"
      rel="noopener noreferrer"
      direction="row"
      sx={(theme) => ({
        gap: 3,
        height: 170,
        p: 3,
        borderRadius: '4px',
        overflow: 'hidden',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        textDecoration: 'none',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <Stack sx={{ height: '100%', aspectRatio: 16 / 9, borderRadius: '4px', overflow: 'hidden' }}>
        <MediaFilePreview mediaFile={mediaFile} previewLabel={fileTypeLabel} />
      </Stack>

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
        <Stack sx={{ minWidth: 0 }}>
          <Typography
            component="h2"
            variant="h6"
            color="textPrimary"
            noWrap
            sx={{ fontWeight: 'bold' }}
          >
            {mediaFile.filename}
          </Typography>

          {description ? (
            <Tooltip title={description} placement="top" arrow disableInteractive>
              <Typography
                component="p"
                color="textSecondary"
                sx={{
                  display: '-webkit-box',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  wordBreak: 'break-word',
                }}
              >
                {description}
              </Typography>
            </Tooltip>
          ) : null}
        </Stack>

        <Stack spacing={1} sx={{ color: 'text.secondary', minHeight: 48 }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minHeight: 20 }}>
            <Chip size="small" label={fileTypeLabel} />
            <Typography variant="body2" noWrap>
              {uploadedAt}
            </Typography>
          </Stack>

          {fileSize ? (
            <Typography variant="body2" noWrap>
              {t('media.size')}: {fileSize}
            </Typography>
          ) : null}
        </Stack>
      </Stack>

      <Box sx={{ alignSelf: 'center', pr: 2 }}>
        <ArrowForwardOutlinedIcon color="action" />
      </Box>
    </Stack>
  )
}

export default MediaFileListCard
