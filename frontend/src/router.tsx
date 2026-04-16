import { Box } from '@mui/material'
import { useLayoutEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'

import Footer from './components/Footer'
import Navbar from './components/Navbar'
import BlogDetailPage from './pages/BlogDetailPage'
import BlogsPage from './pages/BlogsPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import ProductionDetailPage from './pages/ProductionDetailPage'
import ProductionsPage from './pages/ProductionsPage'
import SeriesDetailPage from './pages/SeriesDetailPage'
import SeriesPage from './pages/SeriesPage'

type RouterProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

const ScrollToTop = () => {
  const location = useLocation()

  useLayoutEffect(() => {
    window.scrollTo({ top: 0, left: 0 })
  }, [location.pathname])

  return null
}

const Router = ({ mode, onToggleMode }: RouterProps) => {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar mode={mode} onToggleMode={onToggleMode} />
        <Box component="main" sx={{ flexGrow: 1 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/archive" element={<ProductionsPage />} />
            <Route path="/productions" element={<Navigate to="/archive" replace />} />
            <Route path="/productions/:id" element={<ProductionDetailPage />} />
            <Route path="/series" element={<SeriesPage />} />
            <Route path="/series/:id" element={<SeriesDetailPage />} />
            <Route path="/blogs" element={<BlogsPage />} />
            <Route path="/blogs/:id" element={<BlogDetailPage />} />
            <Route path="/media" element={<Navigate to="/archive" replace />} />
            {/* TODO: Remove after media page is implemented */}
            <Route path="/media/:id" element={<Navigate to="/archive" replace />} />
            {/* TODO: Remove after media page is implemented */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Box>
        <Footer />
      </Box>
    </BrowserRouter>
  )
}

export default Router
