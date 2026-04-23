import DateRangeOutlinedIcon from '@mui/icons-material/DateRangeOutlined'
import { Stack, Typography, useTheme } from '@mui/material'
import { useTranslation } from 'react-i18next'

import MediaFilePreview from './MediaFilePreview'
import {
  formatMediaFileDate,
  formatMediaFileSize,
  getMediaFileDescription,
  getMediaFileTypeLabel,
} from './MediaFileUtils'
import { createCommonStyles } from '../../theme/styles'
import { tokens } from '../../theme/tokens'

import type { MediaFile } from '../../types/MediaFiles'

export interface MediaFileListCardProps {
  mediaFile: MediaFile
}

const MediaFileListCard = ({ mediaFile }: MediaFileListCardProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const { t, i18n } = useTranslation()
  const { language } = i18n

  const uploadedAt = formatMediaFileDate(mediaFile.created_at, language)
  const fileSize = formatMediaFileSize(mediaFile.size_bytes)
  const description = getMediaFileDescription(mediaFile, i18n.language, t)
  const fileTypeLabel = getMediaFileTypeLabel(mediaFile, t)

  return (
    <Stack
      component="a"
      href={mediaFile.file}
      target="_blank"
      rel="noopener noreferrer"
      direction={{ xs: 'column', sm: 'row' }}
      sx={{
        ...commonStyles.cardBase,
        width: '100%',
        minWidth: 0,
        borderRadius: tokens.borderRadius.sm,
        overflow: 'hidden',
        textDecoration: 'none',
        color: 'inherit',
        '&:hover': {
          textDecoration: 'none',
        },
      }}
    >
      <Stack
        sx={{
          p: tokens.spacing.numericMd, // 🔥 ruimte rond preview (zoals blogs)
          flexShrink: 0,
        }}
      >
        <Stack
          sx={{
            width: { xs: '100%', sm: 220 },
            aspectRatio: '16 / 9',
            borderRadius: tokens.borderRadius.sm,
            overflow: 'hidden',
            backgroundColor: 'action.hover',
          }}
        >
          <MediaFilePreview mediaFile={mediaFile} previewLabel={fileTypeLabel} />
        </Stack>
      </Stack>

      <Stack
        sx={{
          flex: 1,
          justifyContent: 'space-between',
          gap: tokens.spacing.numericSm,
          p: tokens.spacing.numericLg,
          minWidth: 0,
        }}
      >
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
            color="text.secondary"
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              wordBreak: 'break-word',
            }}
          >
            {description || fileTypeLabel}
          </Typography>
        </Stack>

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
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
            <DateRangeOutlinedIcon fontSize="inherit" />
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
    </Stack>
  )
}

export default MediaFileListCard
