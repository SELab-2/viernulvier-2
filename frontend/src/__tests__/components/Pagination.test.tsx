import { fireEvent, render, screen } from '@testing-library/react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { I18nextProvider } from 'react-i18next'
import type { ComponentProps } from 'react'
import Pagination from '../../components/Pagination'
import i18n from '../../i18n'

const renderPagination = (props: ComponentProps<typeof Pagination>) => {
  const theme = createTheme()

  return render(
    <I18nextProvider i18n={i18n}>
      <ThemeProvider theme={theme}>
        <Pagination {...props} />
      </ThemeProvider>
    </I18nextProvider>,
  )
}

describe('Pagination', () => {
  it('renders nothing when only one page is available', () => {
    const { container } = renderPagination({
      page: 1,
      pageSize: 24,
      totalItems: 24,
      onPageChange: jest.fn(),
    })

    expect(container).toBeEmptyDOMElement()
  })

  it('renders navigation and current page text when multiple pages exist', () => {
    renderPagination({
      page: 2,
      pageSize: 10,
      totalItems: 35,
      onPageChange: jest.fn(),
    })

    expect(
      screen.getByRole('navigation', { name: 'Paginering van producties' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Pagina 2 van 4')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Huidige pagina, pagina 2' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('emits selected page when user clicks a page button', () => {
    const onPageChange = jest.fn()

    renderPagination({
      page: 1,
      pageSize: 10,
      totalItems: 30,
      onPageChange,
    })

    fireEvent.click(screen.getByRole('button', { name: 'Ga naar pagina 2' }))

    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('disables pagination controls when disabled is true', () => {
    renderPagination({
      page: 1,
      pageSize: 10,
      totalItems: 30,
      onPageChange: jest.fn(),
      disabled: true,
    })

    expect(screen.getByRole('button', { name: 'Ga naar pagina 2' })).toBeDisabled()
  })
})
