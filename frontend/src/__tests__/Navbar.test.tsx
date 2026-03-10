import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Navbar from '../components/Navbar'
import '../i18n'

const renderNavbar = (initialPath = '/') =>
    render(
        <MemoryRouter initialEntries={[initialPath]}>
            <Navbar />
        </MemoryRouter>,
    )

describe('Navbar', () => {
    it('renders the brand logo and Archive label', () => {
        renderNavbar()
        expect(screen.getByAltText('Viernulvier logo')).toBeInTheDocument()
        expect(screen.getByText('/ Archive')).toBeInTheDocument()
    })

    it('renders all navigation links', () => {
        renderNavbar()
        expect(screen.getByRole('link', { name: 'Archive' })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: 'Series' })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: 'Artists' })).toBeInTheDocument()
    })

    it('marks the active route with aria-current="page"', () => {
        renderNavbar('/series')
        expect(screen.getByRole('link', { name: 'Series' })).toHaveAttribute(
            'aria-current',
            'page',
        )
        expect(screen.getByRole('link', { name: 'Archive' })).not.toHaveAttribute(
            'aria-current',
        )
    })

    it('renders language switcher buttons', () => {
        renderNavbar()
        expect(screen.getByRole('button', { name: /en/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /nl/i })).toBeInTheDocument()
    })
})
