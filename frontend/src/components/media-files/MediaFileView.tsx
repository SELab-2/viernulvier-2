import CloseRoundedIcon from '@mui/icons-material/CloseRounded'
import NavigateBeforeRoundedIcon from '@mui/icons-material/NavigateBeforeRounded'
import NavigateNextRoundedIcon from '@mui/icons-material/NavigateNextRounded'
import { Box, IconButton, Modal, Typography, useMediaQuery, useTheme } from '@mui/material'
import { useCallback, useEffect, useState } from 'react'

import MediaFileGrid from './MediaFileGrid'
import MediaFileList from './MediaFileList'
import MediaFilePreview from './MediaFilePreview'
import { tokens } from '../../theme/tokens'
import { DarkMode } from '../../types/Theme'

import type { MediaFile } from '../../types/MediaFiles'
import type { SearchViewMode } from '../searchbar/types'

// Types

export interface MediaFileViewProps {
  mediaFiles: MediaFile[]
  layout?: SearchViewMode
}

interface MediaFileModalProps {
  mediaFiles: MediaFile[]
  selectedIndex: number | null
  onClose: () => void
  onNavigate: (index: number) => void
}

// Modal

const MediaFileModal = ({
  mediaFiles,
  selectedIndex,
  onClose,
  onNavigate,
}: MediaFileModalProps) => {
  const isOpen = selectedIndex !== null
  const selectedFile = selectedIndex !== null ? mediaFiles[selectedIndex] : null

  const hasPrev = selectedIndex !== null && selectedIndex > 0
  const hasNext = selectedIndex !== null && selectedIndex < mediaFiles.length - 1

  useEffect(() => {
    if (!isOpen) {
      return
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && hasPrev) {
        onNavigate((selectedIndex as number) - 1)
      } else if (e.key === 'ArrowRight' && hasNext) {
        onNavigate((selectedIndex as number) + 1)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, hasPrev, hasNext, selectedIndex, onNavigate])

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      slotProps={{
        backdrop: {
          sx: (theme) => ({
            backgroundColor:
              theme.palette.mode === DarkMode
                ? tokens.colors.overlay.modalBackdropDark
                : tokens.colors.overlay.modalBackdropLight,
          }),
        },
      }}
    >
      <Box
        onClick={onClose}
        sx={{
          position: 'fixed',
          inset: 0,
          display: 'grid',
          placeItems: 'center',
          p: { xs: 2, md: 4 },
        }}
      >
        {selectedFile && (
          <Box
            onClick={(e) => e.stopPropagation()}
            sx={{
              width: 'min(1200px, 96vw)',
              maxHeight: '90vh',
              height: '90vh',
              borderRadius: 1.5,
              bgcolor: 'background.paper',
              boxShadow: (theme) => theme.shadows[4],
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* ── Header ── */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                px: 1.5,
                py: 1,
                borderBottom: 1,
                borderColor: 'divider',
                flexShrink: 0,
              }}
            >
              <Typography variant="body1" noWrap sx={{ flex: 1, color: 'text.primary' }}>
                {selectedFile.filename}
              </Typography>

              {mediaFiles.length > 1 && (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.primary',
                    flexShrink: 0,
                    px: 1,
                    py: 0.25,
                    borderRadius: 1,
                    bgcolor: 'action.hover',
                  }}
                >
                  {(selectedIndex as number) + 1} / {mediaFiles.length}
                </Typography>
              )}

              <IconButton
                aria-label="Voorvertoning sluiten"
                onClick={onClose}
                size="small"
                sx={{
                  flexShrink: 0,
                  color: 'text.primary',
                  '&:hover': { bgcolor: 'action.selected' },
                }}
              >
                <CloseRoundedIcon fontSize="small" />
              </IconButton>
            </Box>

            {/* Body: prev | preview | next */}
            {/* Optional description shown when opening a file */}
            {selectedFile &&
              (function getDescriptionBox() {
                const desc =
                  selectedFile.display_description ??
                  (selectedFile.description && Object.values(selectedFile.description)[0]) ??
                  null

                if (!desc) {
                  return null
                }

                return (
                  <Box
                    sx={{
                      px: 2,
                      py: 1,
                      borderBottom: 1,
                      borderColor: 'divider',
                      bgcolor: 'background.default',
                      flexShrink: 0,
                    }}
                  >
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ whiteSpace: 'pre-wrap' }}
                    >
                      {desc}
                    </Typography>
                  </Box>
                )
              })()}
            <Box sx={{ display: 'flex', overflow: 'hidden', flex: 1, minHeight: 0 }}>
              {/* Vorige knop */}
              {mediaFiles.length > 1 && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    px: 0.75,
                    borderRight: 1,
                    borderColor: 'divider',
                    flexShrink: 0,
                  }}
                >
                  <IconButton
                    aria-label="Vorig bestand"
                    disabled={!hasPrev}
                    onClick={() => onNavigate((selectedIndex as number) - 1)}
                    sx={{
                      color: 'text.primary',
                      '&:hover': { bgcolor: 'action.selected' },
                      '&.Mui-disabled': { opacity: 0.3 },
                    }}
                  >
                    <NavigateBeforeRoundedIcon />
                  </IconButton>
                </Box>
              )}

              {/* Preview - eigen scroll met afgeronde scrollbar */}
              <Box
                sx={{
                  flex: 1,
                  minWidth: 0,
                  minHeight: 0,
                  overflow: 'auto',
                  scrollbarWidth: 'thin',
                  scrollbarColor: (theme) => `${theme.palette.action.selected} transparent`,
                  '&::-webkit-scrollbar': { width: 6, height: 6, borderRadius: 3 },
                  '&::-webkit-scrollbar-track': { background: 'transparent', borderRadius: 3 },
                  '&::-webkit-scrollbar-thumb': {
                    bgcolor: 'action.selected',
                    borderRadius: 3,
                    border: '1px solid transparent',
                    backgroundClip: 'content-box',
                  },
                  '&::-webkit-scrollbar-thumb:hover': { bgcolor: 'action.focus' },
                  // Afbeeldingen altijd inpassen in het zichtbare vlak
                  '& img': {
                    maxWidth: '100%',
                    maxHeight: 'calc(90vh - 60px)', // modal hoogte min header
                    objectFit: 'contain',
                    display: 'block',
                    margin: '0 auto',
                  },
                }}
              >
                <MediaFilePreview mediaFile={selectedFile} previewLabel={selectedFile.filename} />
              </Box>

              {/* Volgende knop */}
              {mediaFiles.length > 1 && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    px: 0.75,
                    borderLeft: 1,
                    borderColor: 'divider',
                    flexShrink: 0,
                  }}
                >
                  <IconButton
                    aria-label="Volgend bestand"
                    disabled={!hasNext}
                    onClick={() => onNavigate((selectedIndex as number) + 1)}
                    sx={{
                      color: 'text.primary',
                      '&:hover': { bgcolor: 'action.selected' },
                      '&.Mui-disabled': { opacity: 0.3 },
                    }}
                  >
                    <NavigateNextRoundedIcon />
                  </IconButton>
                </Box>
              )}
            </Box>
          </Box>
        )}
      </Box>
    </Modal>
  )
}

// Main component

const MediaFileView = ({ mediaFiles, layout = 'list' }: MediaFileViewProps) => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  const activeLayout: SearchViewMode = isSmall ? 'grid' : layout

  const handleOpen = useCallback(
    (file: MediaFile) => {
      const index = mediaFiles.findIndex((f) => f === file)
      if (index !== -1) {
        setSelectedIndex(index)
      }
    },
    [mediaFiles],
  )

  const handleClose = useCallback(() => setSelectedIndex(null), [])
  const handleNavigate = useCallback((index: number) => setSelectedIndex(index), [])

  if (mediaFiles.length === 0) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 8 }}>
        <Typography variant="body2" color="text.secondary">
          Geen mediabestanden gevonden.
        </Typography>
      </Box>
    )
  }

  return (
    <>
      {activeLayout === 'list' ? (
        <MediaFileList mediaFiles={mediaFiles} onOpenMediaFile={handleOpen} />
      ) : (
        <MediaFileGrid mediaFiles={mediaFiles} onOpenMediaFile={handleOpen} />
      )}

      <MediaFileModal
        mediaFiles={mediaFiles}
        selectedIndex={selectedIndex}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    </>
  )
}

export default MediaFileView
