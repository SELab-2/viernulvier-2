import { useMediaQuery, useTheme } from '@mui/material'

import MediaFileGrid from './MediaFileGrid'
import MediaFileList from './MediaFileList'

import type { MediaFile } from '../../types/MediaFiles'
import type { SearchViewMode } from '../searchbar/types'

export interface MediaFileViewProps {
  mediaFiles: MediaFile[]
  layout?: SearchViewMode
}

const MediaFileView = ({ mediaFiles, layout = 'list' }: MediaFileViewProps) => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))

  const activeLayout: SearchViewMode = isSmall ? 'grid' : layout

  if (activeLayout === 'list') {
    return <MediaFileList mediaFiles={mediaFiles} />
  }

  return <MediaFileGrid mediaFiles={mediaFiles} />
}

export default MediaFileView
