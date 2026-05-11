import MediaFileListCard from './MediaFileListCard'
import GenericList from '../../../shared/components/GenericList'

import type { MediaFile } from '../../../types/MediaFiles'

export interface MediaFileListProps {
  mediaFiles: MediaFile[]
}

const MediaFileList = ({ mediaFiles }: MediaFileListProps) => {
  return (
    <GenericList
      items={mediaFiles}
      getKey={(mediaFile) => mediaFile.id}
      renderItem={(mediaFile) => <MediaFileListCard mediaFile={mediaFile} />}
    />
  )
}

export default MediaFileList
