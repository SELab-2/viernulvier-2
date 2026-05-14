import { Box } from '@mui/material'

import MediaFileGridCard from './MediaFileGridCard'
import GenericGrid from '../../../shared/components/GenericGrid'

import type { MediaFile } from '../../../types/MediaFiles'

/**
 * Props for MediaFileGrid component.
 */
export interface MediaFileGridProps {
  mediaFiles: MediaFile[]
}

/**
 * Renders a grid of media files using GenericGrid.
 *
 * Each item is rendered using MediaFileGridCard.
 * The wrapper Box ensures centered alignment of grid items.
 */
const MediaFileGrid = ({ mediaFiles }: MediaFileGridProps) => {
  return (
    <Box
      sx={{
        width: '100%',
        '& > *': {
          justifyContent: 'center !important',
        },
      }}
    >
      {/* Generic grid renderer for media files */}
      <GenericGrid
        items={mediaFiles}
        getKey={(mediaFile) => mediaFile.id}
        renderItem={(mediaFile) => <MediaFileGridCard mediaFile={mediaFile} />}
      />
    </Box>
  )
}

export default MediaFileGrid
