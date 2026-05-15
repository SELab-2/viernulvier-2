import MediaFileListCard from './MediaFileListCard'
import GenericList from '../GenericList'

import type { MediaFile } from '../../types/MediaFiles'

export interface MediaFileListProps {
  mediaFiles: MediaFile[]
  onOpenMediaFile?: (mediaFile: MediaFile) => void
}

const MediaFileList = ({ mediaFiles, onOpenMediaFile }: MediaFileListProps) => {
  return (
    <GenericList
      items={mediaFiles}
      getKey={(mediaFile) => mediaFile.id}
      renderItem={(mediaFile) => (
        <MediaFileListCard mediaFile={mediaFile} onOpen={onOpenMediaFile} />
      )}
    />
  )
}

export default MediaFileList
