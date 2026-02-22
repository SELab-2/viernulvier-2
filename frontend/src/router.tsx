import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import EventsPage from './pages/EventsPage'
import EventDetailPage from './pages/EventDetailPage'
import ProductionsPage from './pages/ProductionsPage'
import ProductionDetailPage from './pages/ProductionDetailPage'
import Navbar from './components/Navbar'

const Router = () => {
    return (
        <BrowserRouter>
            <Navbar />
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/events" element={<EventsPage />} />
                <Route path="/events/:id" element={<EventDetailPage />} />
                <Route path="/productions" element={<ProductionsPage />} />
                <Route path="/productions/:id" element={<ProductionDetailPage />} />
            </Routes>
        </BrowserRouter>
    )
}

export default Router
