import type { Blog } from '../types/Blogs'
import BlogListCard from './BlogListCard'
import GenericList from './GenericList'

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
