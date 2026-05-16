import { Box } from '@mui/material'

import MediaFileGridCard from './MediaFileGridCard'
import GenericGrid from '../GenericGrid'

import type { MediaFile } from '../../types/MediaFiles'

export interface MediaFileGridProps {
  mediaFiles: MediaFile[]
  onOpenMediaFile?: (mediaFile: MediaFile) => void
}

const MediaFileGrid = ({ mediaFiles, onOpenMediaFile }: MediaFileGridProps) => {
  return (
    <Box
      sx={{
        width: '100%',
        '& > *': {
          justifyContent: 'center !important',
        },
      }}
    >
      <GenericGrid
        items={mediaFiles}
        getKey={(mediaFile) => mediaFile.id}
        renderItem={(mediaFile) => (
          <MediaFileGridCard mediaFile={mediaFile} onOpen={onOpenMediaFile} />
        )}
      />
    </Box>
  )
}

export default MediaFileGrid
