import BlogGridCard from './BlogGridCard'
import GenericGrid from '../../../shared/components/GenericGrid'

import type { Blog } from '../../../types/Blogs'

/**
 * Props for BlogGrid component.
 * Contains a list of blogs to render in a grid layout.
 */
export interface BlogGridProps {
  blogs: Blog[]
}

/**
 * BlogGrid
 *
 * Wrapper around GenericGrid that renders blogs in a responsive grid layout
 * using BlogGridCard as the visual representation.
 */
const BlogGrid = ({ blogs }: BlogGridProps) => {
  return (
    <GenericGrid
      items={blogs}
      getKey={(blog) => blog.id}
      renderItem={(blog) => <BlogGridCard blog={blog} />}
    />
  )
}

export default BlogGrid
