import OpenInNewOutlinedIcon from '@mui/icons-material/OpenInNewOutlined'
import { Chip, Stack, Tooltip, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import MediaFilePreview from './MediaFilePreview'
import {
  formatMediaFileDate,
  formatMediaFileSize,
  getMediaFileDescription,
  getMediaFileTypeLabel,
} from './MediaFileUtils'

import type { MediaFile } from '../../types/MediaFiles'

export interface MediaFileGridCardProps {
  mediaFile: MediaFile
}

const MediaFileGridCard = ({ mediaFile }: MediaFileGridCardProps) => {
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
      sx={(theme) => ({
        width: 350,
        borderRadius: 4,
        overflow: 'hidden',
        textDecoration: 'none',
        border: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: theme.shadows[3],
        },
      })}
    >
      <Stack sx={{ aspectRatio: 16 / 9 }}>
        <MediaFilePreview mediaFile={mediaFile} previewLabel={fileTypeLabel} />
      </Stack>

      <Stack sx={{ flex: 1, justifyContent: 'space-between', gap: 1, p: 3 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', color: 'text.secondary' }}>
          <Chip size="small" label={fileTypeLabel} />
          <OpenInNewOutlinedIcon fontSize="small" />
        </Stack>

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

        <Stack direction="row" spacing={1.5} sx={{ color: 'text.secondary', minHeight: 20 }}>
          <Typography variant="body2" noWrap>
            {uploadedAt}
          </Typography>
          {fileSize ? (
            <Typography variant="body2" noWrap>
              {t('media.size')}: {fileSize}
            </Typography>
          ) : null}
        </Stack>
      </Stack>
    </Stack>
  )
}

export default MediaFileGridCard
