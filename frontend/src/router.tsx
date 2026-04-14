import { Box } from '@mui/material'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import Footer from './components/Footer'
import Navbar from './components/Navbar'
import BlogsPage from './pages/BlogsPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import ProductionDetailPage from './pages/ProductionDetailPage'
import SeriesDetailPage from './pages/SeriesDetailPage'
import SeriesPage from './pages/SeriesPage'

type RouterProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

const Router = ({ mode, onToggleMode }: RouterProps) => {
  return (
    <BrowserRouter>
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar mode={mode} onToggleMode={onToggleMode} />
        <Box component="main" sx={{ flexGrow: 1 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/productions" element={<Navigate to="/" replace />} />
            <Route path="/productions/:id" element={<ProductionDetailPage />} />
            <Route path="/series" element={<SeriesPage />} />
            <Route path="/series/:id" element={<SeriesDetailPage />} />
            <Route path="/blogs" element={<BlogsPage />} />
            <Route path="/blogs/:id" element={<BlogDetailPage />} />
            <Route path="/media" element={<Navigate to="/" replace />} />
            {/* TODO: Remove after media page is implemented */}
            <Route path="/media/:id" element={<Navigate to="/" replace />} />
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
