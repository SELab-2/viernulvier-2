import BlogListCard from './BlogListCard'
import GenericList from '../../../shared/components/GenericList'

import type { Blog } from '../../../types/Blogs'

/**
 * Props for BlogList component.
 * Contains an array of blog items to render.
 */
export interface BlogListProps {
  blogs: Blog[]
}

/**
 * BlogList
 *
 * Simple wrapper around GenericList that renders blogs
 * using the BlogListCard component in a vertical list layout.
 */
const BlogList = ({ blogs }: BlogListProps) => {
  return (
    <GenericList
      items={blogs}
      getKey={(blog) => blog.id}
      renderItem={(blog) => <BlogListCard blog={blog} />}
    />
  )
}

export default BlogList
