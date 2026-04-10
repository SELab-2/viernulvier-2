import { Box, useTheme } from '@mui/material'
import { createCommonStyles } from '../theme/styles'
import type { Blog } from '../types/Blogs'
import BlogGridCard from './BlogGridCard'

export interface BlogGridProps {
  blogs: Blog[]
}

const BlogGrid = ({ blogs }: BlogGridProps) => {
  const theme = useTheme()
  const commonStyles = createCommonStyles(theme)

  return (
    <Box sx={commonStyles.gridContainer}>
      {blogs.map((blog) => (
        <BlogGridCard key={blog.id} blog={blog} />
      ))}
    </Box>
  )
}

export default BlogGrid
