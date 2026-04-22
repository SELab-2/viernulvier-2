import { ThemeProvider, createTheme } from '@mui/material/styles'
import { fireEvent, render, screen } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'

import Pagination from '../../components/Pagination'
import i18n from '../../i18n'

import type { ComponentProps } from 'react'

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
  beforeEach(async () => {
    await i18n.changeLanguage('nl')
  })

  it('renders nothing when only one page is available', () => {
    const { container } = renderPagination({
      page: 1,
      pageSize: 24,
      totalItems: 24,
      onPageChange: jest.fn(),
    })

    expect(container).toBeEmptyDOMElement()
  })

  it('renders navigation, page input, and total pages label when multiple pages exist', () => {
    renderPagination({
      page: 2,
      pageSize: 10,
      totalItems: 35,
      onPageChange: jest.fn(),
    })

    expect(
      screen.getByRole('navigation', { name: 'Paginering van producties' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Huidige pagina, pagina 2' })).toHaveValue('2')
    expect(screen.getByText('van 4')).toBeInTheDocument()
  })

  it('emits selected page when user clicks the next button', () => {
    const onPageChange = jest.fn()

    renderPagination({
      page: 1,
      pageSize: 10,
      totalItems: 30,
      onPageChange,
    })

    fireEvent.click(screen.getByRole('button', { name: 'Ga naar volgende pagina' }))

    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('does not emit on change while typing and commits on Enter', () => {
    const onPageChange = jest.fn()

    renderPagination({
      page: 2,
      pageSize: 10,
      totalItems: 50,
      onPageChange,
    })

    const input = screen.getByRole('textbox', { name: 'Huidige pagina, pagina 2' })
    fireEvent.change(input, { target: { value: '5' } })

    expect(onPageChange).not.toHaveBeenCalled()
    expect(input).toHaveValue('5')

    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onPageChange).toHaveBeenCalledWith(5)
  })

  it('resets invalid page input to the active page on blur', () => {
    const onPageChange = jest.fn()

    renderPagination({
      page: 3,
      pageSize: 10,
      totalItems: 50,
      onPageChange,
    })

    const input = screen.getByRole('textbox', { name: 'Huidige pagina, pagina 3' })
    fireEvent.change(input, { target: { value: 'abc' } })
    fireEvent.blur(input)

    expect(onPageChange).not.toHaveBeenCalled()
    expect(input).toHaveValue('3')
  })

  it('disables pagination controls when disabled is true', () => {
    renderPagination({
      page: 1,
      pageSize: 10,
      totalItems: 30,
      onPageChange: jest.fn(),
      disabled: true,
    })

    expect(screen.getByRole('button', { name: 'Ga naar eerste pagina' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Ga naar vorige pagina' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Ga naar volgende pagina' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Ga naar laatste pagina' })).toBeDisabled()
    expect(screen.getByRole('textbox', { name: 'Huidige pagina, pagina 1' })).toBeDisabled()
  })
})
