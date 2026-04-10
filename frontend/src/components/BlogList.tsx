import { Stack } from '@mui/material'
import type { Blog } from '../types/Blogs'
import BlogListCard from './BlogListCard'

export interface BlogListProps {
  blogs: Blog[]
}

const BlogList = ({ blogs }: BlogListProps) => {
  return (
    <Stack spacing={2}>
      {blogs.map((blog) => (
        <BlogListCard key={blog.id} blog={blog} />
      ))}
    </Stack>
  )
}

export default BlogList
