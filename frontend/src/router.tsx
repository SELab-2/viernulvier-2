import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import HomePage from './pages/HomePage'
import SeriesPage from './pages/SeriesPage'
import SeriesDetailPage from './pages/SeriesDetailPage'
import ArtistsPage from './pages/ArtistsPage'
import ArtistDetailPage from './pages/ArtistDetailPage'
import Navbar from './components/Navbar'

type RouterProps = {
  mode: 'light' | 'dark'
  onToggleMode: () => void
}

const Router = ({ mode, onToggleMode }: RouterProps) => {
  return (
    <BrowserRouter>
      <Navbar mode={mode} onToggleMode={onToggleMode} />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/series" element={<SeriesPage />} />
        <Route path="/series/:id" element={<SeriesDetailPage />} />
        <Route path="/artists" element={<ArtistsPage />} />
        <Route path="/artists/:id" element={<ArtistDetailPage />} />
        <Route path="/events" element={<Navigate to="/series" replace />} />
        <Route path="/events/:id" element={<Navigate to="/series" replace />} />
        <Route path="/productions" element={<Navigate to="/artists" replace />} />
        <Route path="/productions/:id" element={<Navigate to="/artists" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default Router
