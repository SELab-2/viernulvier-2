import MediaFileListCard from './MediaFileListCard'
import GenericList from '../../../shared/components/GenericList'

import type { MediaFile } from '../../../types/MediaFiles'

/**
 * Props for MediaFileList component.
 */
export interface MediaFileListProps {
  mediaFiles: MediaFile[]
}

/**
 * Renders a simple list of media files using GenericList.
 *
 * Each item is rendered via MediaFileListCard.
 * The list is keyed by mediaFile.id to ensure stable rendering.
 */
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
