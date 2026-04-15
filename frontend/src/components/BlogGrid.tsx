import BlogGridCard from './BlogGridCard'
import GenericGrid from './GenericGrid'

import type { Blog } from '../types/Blogs'

export interface BlogGridProps {
  blogs: Blog[]
}

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
