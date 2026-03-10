import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Navbar from '../components/Navbar'
import '../i18n'

const renderNavbar = (initialPath = '/') =>
    render(
        <MemoryRouter initialEntries={[initialPath]}>
            <Navbar mode="light" onToggleMode={jest.fn()} />
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
        expect(screen.getByRole('link', { name: 'Archief' })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: 'Reeksen' })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: 'Artiesten' })).toBeInTheDocument()
    })

    it('marks the active route with aria-current="page"', () => {
        renderNavbar('/series')
        expect(screen.getByRole('link', { name: 'Reeksen' })).toHaveAttribute(
            'aria-current',
            'page',
        )
        expect(screen.getByRole('link', { name: 'Archief' })).not.toHaveAttribute(
            'aria-current',
        )
    })

    it('renders language switcher button', () => {
        renderNavbar()
        const langButton = screen.getByRole('button', { name: /switch language/i })
        expect(langButton).toBeInTheDocument()
    })

    it('renders theme toggle button', () => {
        renderNavbar()
        expect(screen.getByRole('button', { name: /switch to dark mode/i })).toBeInTheDocument()
    })
})
