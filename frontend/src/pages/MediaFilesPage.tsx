import DescriptionIcon from '@mui/icons-material/Description'
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined'
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf'
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Chip,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import MediaFilesPageSkeleton from './MediaFilesPageSkeleton'
import CollectionPageLayout from '../components/CollectionPageLayout'
import FloatingAlert from '../components/FloatingAlert'
import { useSearchBarUrlState } from '../components/searchbar/useSearchBarUrlState'
import { ApiError } from '../services/ApiTypes'
import { getMediaFiles } from '../services/media_files/MediaFiles'
import { getLocalizedValue } from '../utils/localization'

import type { SearchSortDirection, SearchSortTarget } from '../components/searchbar/types'
import type { MediaFile } from '../types/MediaFiles'

const PAGE_SIZE = 12

const MEDIA_SORT_TARGET_OPTIONS: Array<{ value: SearchSortTarget; labelKey: string }> = [
  { value: 'date', labelKey: 'searchbar.sort.date' },
]

const getOrderingValue = (sortDirection: SearchSortDirection): string =>
  sortDirection === 'desc' ? '-created_at' : 'created_at'

const formatDate = (value: string, locale: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

const formatSize = (value: number | null): string | null => {
  if (value === null || value <= 0) {
    return null
  }

  if (value < 1024) {
    return `${value} B`
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

const getFileTypeLabel = (
  mediaFile: MediaFile,
  t: ReturnType<typeof useTranslation>['t'],
): string => {
  return t(`media.fileType.${mediaFile.file_type}`)
}

const getMediaFileDescription = (mediaFile: MediaFile, locale: string): string | null => {
  return getLocalizedValue(mediaFile.description, locale) || mediaFile.display_description || null
}

const MediaFilePreview = ({
  mediaFile,
  t,
  isGrid,
}: {
  mediaFile: MediaFile
  t: ReturnType<typeof useTranslation>['t']
  isGrid: boolean
}) => {
  const previewHeight = isGrid ? 220 : 160

  if (mediaFile.file_type === 'image') {
    return (
      <CardMedia
        component="img"
        image={mediaFile.file}
        alt={mediaFile.filename}
        sx={{
          width: '100%',
          height: previewHeight,
          objectFit: isGrid ? 'cover' : 'contain',
          objectPosition: 'center',
          backgroundColor: 'grey.100',
        }}
      />
    )
  }

  const Icon = mediaFile.file_type === 'pdf' ? PictureAsPdfIcon : InsertDriveFileOutlinedIcon

  return (
    <Box
      sx={{
        width: '100%',
        height: previewHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'action.hover',
        borderBottom: isGrid ? 1 : 0,
        borderRight: isGrid ? 0 : 1,
        borderColor: 'divider',
      }}
    >
      <Stack spacing={1} sx={{ alignItems: 'center', color: 'text.secondary' }}>
        <Icon sx={{ fontSize: 56 }} />
        <Typography variant="body2">{getFileTypeLabel(mediaFile, t)}</Typography>
      </Stack>
    </Box>
  )
}

const MediaFileCard = ({
  mediaFile,
  layout,
  locale,
  t,
}: {
  mediaFile: MediaFile
  layout: 'grid' | 'list'
  locale: string
  t: ReturnType<typeof useTranslation>['t']
}) => {
  const fileSize = formatSize(mediaFile.size_bytes)
  const uploadedAt = formatDate(mediaFile.created_at, locale)
  const isGrid = layout === 'grid'
  const description = getMediaFileDescription(mediaFile, locale)

  return (
    <Card
      variant="outlined"
      sx={{
        height: '100%',
        display: 'flex',
        borderRadius: 3,
        overflow: 'hidden',
      }}
    >
      <CardActionArea
        component="a"
        href={mediaFile.file}
        target="_blank"
        rel="noopener noreferrer"
        sx={{
          display: 'flex',
          flexDirection: isGrid ? 'column' : { xs: 'column', sm: 'row' },
          alignItems: 'stretch',
          height: '100%',
        }}
      >
        <Box
          sx={{
            width: isGrid ? '100%' : { xs: '100%', sm: 240 },
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            alignSelf: 'stretch',
            p: isGrid ? 0 : 2,
          }}
        >
          <MediaFilePreview mediaFile={mediaFile} t={t} isGrid={isGrid} />
        </Box>

        <CardContent
          sx={{
            flex: 1,
            minWidth: 0,
            py: 2,
            px: 2.5,
            display: 'flex',
          }}
        >
          <Stack spacing={1.25} sx={{ width: '100%' }}>
            <Stack
              direction="row"
              spacing={1}
              sx={{
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                rowGap: 1,
              }}
            >
              <Chip
                size="small"
                icon={<DescriptionIcon />}
                label={getFileTypeLabel(mediaFile, t)}
              />
              <Typography variant="caption" color="text.secondary">
                {uploadedAt}
              </Typography>
            </Stack>

            <Typography
              variant="h6"
              component="h3"
              sx={{
                fontSize: isGrid ? '1rem' : '1.05rem',
                fontWeight: 700,
                lineHeight: 1.3,
                wordBreak: 'break-word',
              }}
            >
              {mediaFile.filename}
            </Typography>

            {description ? (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  display: '-webkit-box',
                  overflow: 'hidden',
                  WebkitLineClamp: isGrid ? 2 : 3,
                  WebkitBoxOrient: 'vertical',
                }}
              >
                {description}
              </Typography>
            ) : null}

            {fileSize ? (
              <Typography variant="body2" color="text.secondary">
                {t('media.size')}: {fileSize}
              </Typography>
            ) : null}
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}

const MediaFilesResults = ({
  items,
  layout,
  locale,
  t,
}: {
  items: MediaFile[]
  layout: 'grid' | 'list'
  locale: string
  t: ReturnType<typeof useTranslation>['t']
}) => {
  if (layout === 'list') {
    return (
      <Stack spacing={2}>
        {items.map((mediaFile) => (
          <MediaFileCard
            key={mediaFile.id}
            mediaFile={mediaFile}
            layout="list"
            locale={locale}
            t={t}
          />
        ))}
      </Stack>
    )
  }

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, minmax(0, 1fr))',
          lg: 'repeat(3, minmax(0, 1fr))',
        },
        gap: 2,
      }}
    >
      {items.map((mediaFile) => (
        <MediaFileCard
          key={mediaFile.id}
          mediaFile={mediaFile}
          layout="grid"
          locale={locale}
          t={t}
        />
      ))}
    </Box>
  )
}

const MediaFilesPage = () => {
  const { t, i18n } = useTranslation()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  const {
    searchValue,
    sortTarget,
    sortDirection,
    viewMode,
    page,
    setSearchValue,
    setSortTarget,
    setSortDirection,
    setViewMode,
    setPage,
  } = useSearchBarUrlState({ isMobile })

  const [isLoading, setIsLoading] = useState(true)
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showFallbackError, setShowFallbackError] = useState(false)
  const [isFloatingErrorOpen, setIsFloatingErrorOpen] = useState(false)
  const [retryKey, setRetryKey] = useState(0)
  const [searchDraft, setSearchDraft] = useState(searchValue)

  const previousOrderingRef = useRef<string | null>(null)

  const renderedErrorMessage = showFallbackError ? t('media.error.fallback') : errorMessage
  const floatingErrorMessage = t('media.error.notification')
  const ordering = useMemo(() => getOrderingValue(sortDirection), [sortDirection])

  useEffect(() => {
    setSearchDraft(searchValue)
  }, [searchValue])

  useEffect(() => {
    if (sortTarget === 'name') {
      setSortTarget('date')
    }
  }, [setSortTarget, sortTarget])

  useEffect(() => {
    const previousOrdering = previousOrderingRef.current

    if (previousOrdering !== null && previousOrdering !== ordering && page !== 1) {
      setPage(1)
    }

    previousOrderingRef.current = ordering
  }, [ordering, page, setPage])

  useEffect(() => {
    let isActive = true

    const fetchMediaFiles = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      setShowFallbackError(false)
      setIsFloatingErrorOpen(false)

      try {
        const trimmedSearchValue = searchValue.trim()

        const response = await getMediaFiles({
          page,
          pageSize: PAGE_SIZE,
          filters: {
            search: trimmedSearchValue || undefined,
            description: trimmedSearchValue || undefined,
            ordering,
          },
        })

        if (!isActive) {
          return
        }

        setMediaFiles(response.results)
        setTotalCount(response.count)
      } catch (error: unknown) {
        if (!isActive) {
          return
        }

        if (error instanceof ApiError) {
          setErrorMessage(error.message)
          setShowFallbackError(true)
        } else {
          setErrorMessage(null)
          setShowFallbackError(true)
        }

        setIsFloatingErrorOpen(true)
        setMediaFiles([])
        setTotalCount(0)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void fetchMediaFiles()

    return () => {
      isActive = false
    }
  }, [ordering, page, retryKey, searchValue])

  const onRetry = () => {
    setIsFloatingErrorOpen(false)
    setRetryKey((value) => value + 1)
  }

  const onFloatingErrorClose = () => {
    setIsFloatingErrorOpen(false)
  }

  const onSearchSubmit = (value: string) => {
    const nextQuery = value.trim()

    if (nextQuery === searchValue.trim()) {
      setRetryKey((current) => current + 1)
      return
    }

    if (page !== 1) {
      setPage(1)
    }

    setSearchValue(nextQuery)
  }

  return (
    <>
      <CollectionPageLayout
        isMobile={isMobile}
        searchPlaceholder={t('media.searchPlaceholder')}
        searchValue={searchDraft}
        onSearchChange={setSearchDraft}
        onSearchSubmit={onSearchSubmit}
        sortTarget={sortTarget}
        onSortTargetChange={setSortTarget}
        sortDirection={sortDirection}
        onSortDirectionChange={setSortDirection}
        sortTargetOptions={MEDIA_SORT_TARGET_OPTIONS}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        resultCount={totalCount}
        resultsRegionAriaLabel={t('media.resultsRegionLabel')}
        isLoading={isLoading}
        loadingLabel={t('media.loading')}
        loadingContent={<MediaFilesPageSkeleton />}
        errorMessage={renderedErrorMessage}
        retryLabel={t('media.error.retry')}
        onRetry={onRetry}
        emptyTitle={t('media.empty.title')}
        emptyDescription={t('media.empty.description')}
        hasResults={mediaFiles.length > 0}
        resultsContent={
          <MediaFilesResults items={mediaFiles} layout={viewMode} locale={i18n.language} t={t} />
        }
        page={page}
        pageSize={PAGE_SIZE}
        totalItems={totalCount}
        onPageChange={setPage}
        paginationI18nKeyPrefix="media.pagination"
      />

      <FloatingAlert
        open={isFloatingErrorOpen}
        onClose={onFloatingErrorClose}
        severity="error"
        message={floatingErrorMessage}
      />
    </>
  )
}

export default MediaFilesPage
