import { useMediaQuery, useTheme } from '@mui/material'

import BlogGrid from './BlogGrid'
import BlogList from './BlogList'

import type { Blog } from '../types/Blogs'
import type { SearchViewMode } from './searchbar/types'

export interface BlogViewProps {
  blogs: Blog[]
  layout?: SearchViewMode
}

const BlogView = ({ blogs, layout = 'list' }: BlogViewProps) => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('md'))

  const activeLayout: SearchViewMode = isSmall ? 'grid' : layout

  if (activeLayout === 'list') {
    return <BlogList blogs={blogs} />
  }

  return <BlogGrid blogs={blogs} />
}

export default BlogView
