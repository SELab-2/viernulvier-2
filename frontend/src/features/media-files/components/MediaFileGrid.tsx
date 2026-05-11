import { Box } from '@mui/material'

import MediaFileGridCard from './MediaFileGridCard'
import GenericGrid from '../../../shared/components/GenericGrid'

import type { MediaFile } from '../../../types/MediaFiles'

export interface MediaFileGridProps {
  mediaFiles: MediaFile[]
}

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
      <GenericGrid
        items={mediaFiles}
        getKey={(mediaFile) => mediaFile.id}
        renderItem={(mediaFile) => <MediaFileGridCard mediaFile={mediaFile} />}
      />
    </Box>
  )
}

export default MediaFileGrid
