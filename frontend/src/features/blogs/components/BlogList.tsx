import BlogListCard from './BlogListCard'
import GenericList from '../../../shared/components/GenericList'

import type { Blog } from '../../../types/Blogs'

export interface BlogListProps {
  blogs: Blog[]
}

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
