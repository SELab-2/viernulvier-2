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
import { getPublicMediaFileUrl } from '../../utils/mediaFileUrls'

import type { MediaFile } from '../../types/MediaFiles'

export interface MediaFileGridCardProps {
  mediaFile: MediaFile
}

const MediaFileGridCard = ({ mediaFile }: MediaFileGridCardProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)
  const { t, i18n } = useTranslation()
  const { language } = i18n

  const uploadedAt = formatMediaFileDate(mediaFile.created_at, language)
  const fileSize = formatMediaFileSize(mediaFile.size_bytes)
  const description = getMediaFileDescription(mediaFile, i18n.language, t)
  const fileTypeLabel = getMediaFileTypeLabel(mediaFile, t)
  const fileUrl = getPublicMediaFileUrl(mediaFile.file)

  return (
    <Stack
      component="a"
      href={fileUrl}
      sx={{
        ...commonStyles.cardBase,
        width: { xs: '100%', sm: 350 },
        maxWidth: '100%',
        height: '100%',
        borderRadius: tokens.card.borderRadius,
        overflow: 'hidden',
        textDecoration: 'none',
        color: 'inherit',
        '&:hover': {
          textDecoration: 'none',
        },
      }}
    >
      <Stack sx={{ aspectRatio: 16 / 9, overflow: 'hidden' }}>
        <MediaFilePreview mediaFile={mediaFile} previewLabel={fileTypeLabel} />
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
            noWrap
            sx={{ fontWeight: 'bold' }}
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
              minHeight: 60,
              wordBreak: 'break-word',
            }}
          >
            {description || fileTypeLabel}
          </Typography>
        </Stack>

        {/* Footer: links op mobiel, space-between op desktop */}
        <Stack
          direction="row"
          sx={{
            alignItems: 'center',
            justifyContent: { xs: 'flex-start', sm: 'space-between' },
            color: 'text.secondary',
            minWidth: 0,
            flexWrap: 'wrap',
            rowGap: 0.5,
            columnGap: 1,
          }}
        >
          <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', minWidth: 0 }}>
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

export default MediaFileGridCard
