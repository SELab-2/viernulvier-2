import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Box } from '@mui/material'
import Footer from './components/Footer'
import Navbar from './components/Navbar'
import ArtistDetailPage from './pages/ArtistDetailPage'
import ArtistsPage from './pages/ArtistsPage'
import BlogsPage from './pages/BlogsPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import SeriesDetailPage from './pages/SeriesDetailPage'
import SeriesPage from './pages/SeriesPage'
import ProductionDetailPage from './pages/ProductionDetailPage'
import BlogDetailPage from './pages/BlogDetailPage'

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
            <Route path="/series" element={<SeriesPage />} />
            <Route path="/series/:id" element={<SeriesDetailPage />} />
            <Route path="/artists" element={<ArtistsPage />} />
            <Route path="/artists/:id" element={<ArtistDetailPage />} />
            <Route path="/blogs" element={<BlogsPage />} />
            <Route path="/blogs/:id" element={<BlogDetailPage />} />
            <Route path="/events" element={<Navigate to="/series" replace />} />
            <Route path="/events/:id" element={<Navigate to="/series" replace />} />
            <Route path="/productions" element={<Navigate to="/artists" replace />} />
            <Route path="/productions/:id" element={<ProductionDetailPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Box>
        <Footer />
      </Box>
    </BrowserRouter>
  )
}

export default Router
