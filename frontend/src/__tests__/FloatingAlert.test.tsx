import { render, screen, waitFor } from '@testing-library/react'
import FloatingAlert from '../components/FloatingAlert'

describe('FloatingAlert', () => {
  it('renders floating alert when open is true', () => {
    render(<FloatingAlert open message="Error occurred" onClose={jest.fn()} />)
    expect(screen.getByText('Error occurred')).toBeInTheDocument()
    expect(screen.getByTestId('floating-alert')).toBeInTheDocument()
  })

  it('renders title and message together', () => {
    render(
      <FloatingAlert
        open
        title="Attention"
        message="Please review this warning"
        onClose={jest.fn()}
      />,
    )
    expect(screen.getByText('Attention')).toBeInTheDocument()
    expect(screen.getByText('Please review this warning')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn()
    const { getByRole } = render(
      <FloatingAlert open message="Message" onClose={onClose} severity="info" />,
    )
    const closeButton = getByRole('button', { name: /close notification/i })
    closeButton.click()
    expect(onClose).toHaveBeenCalled()
  })

  it('auto-closes after specified duration', async () => {
    const onClose = jest.fn()
    render(<FloatingAlert open message="Auto-dismiss" onClose={onClose} autoCloseDuration={100} />)

    await waitFor(
      () => {
        expect(onClose).toHaveBeenCalled()
      },
      { timeout: 500 },
    )
  })

  it('renders all severity levels', () => {
    const severities: FloatingAlertSeverity[] = ['error', 'warning', 'info', 'success']
    severities.forEach((severity) => {
      const { unmount } = render(
        <FloatingAlert
          open
          message={`${severity} message`}
          onClose={jest.fn()}
          severity={severity}
        />,
      )
      expect(screen.getByText(`${severity} message`)).toBeInTheDocument()
      unmount()
    })
  })

  it('supports custom position', () => {
    render(
      <FloatingAlert
        open
        message="Top right alert"
        onClose={jest.fn()}
        position={{ vertical: 'top', horizontal: 'right' }}
      />,
    )
    expect(screen.getByText('Top right alert')).toBeInTheDocument()
  })
})

type FloatingAlertSeverity = 'error' | 'warning' | 'info' | 'success'
