import { fireEvent, render, screen, within } from '@testing-library/react'

import FloatingAlertStack from '../../../shared/components/FloatingAlertStack'

const alerts = [
  { id: 1, open: true, message: 'First alert', severity: 'info' as const },
  { id: 2, open: true, message: 'Second alert', severity: 'error' as const },
  { id: 3, open: true, message: 'Third alert', severity: 'success' as const },
]

describe('FloatingAlertStack', () => {
  it('renders multiple alerts under each other', () => {
    render(<FloatingAlertStack alerts={alerts} onClose={jest.fn()} />)

    expect(screen.getByTestId('floating-alert-stack')).toBeInTheDocument()
    expect(screen.getAllByTestId('floating-alert')).toHaveLength(3)
    expect(screen.getByText('First alert')).toBeInTheDocument()
    expect(screen.getByText('Second alert')).toBeInTheDocument()
    expect(screen.getByText('Third alert')).toBeInTheDocument()
  })

  it('closes the selected alert by id', () => {
    const onClose = jest.fn()
    render(<FloatingAlertStack alerts={alerts} onClose={onClose} />)

    const secondAlert = screen.getByText('Second alert').closest('[data-testid="floating-alert"]')
    expect(secondAlert).not.toBeNull()

    fireEvent.click(within(secondAlert as HTMLElement).getByRole('button', { name: /close/i }))

    expect(onClose).toHaveBeenCalledWith(2)
  })

  it('compacts remaining alerts when one is removed', () => {
    const { rerender } = render(<FloatingAlertStack alerts={alerts} onClose={jest.fn()} />)

    rerender(
      <FloatingAlertStack alerts={alerts.filter((alert) => alert.id !== 2)} onClose={jest.fn()} />,
    )

    const renderedAlerts = screen.getAllByTestId('floating-alert')
    expect(renderedAlerts).toHaveLength(2)
    expect(renderedAlerts[0]).toHaveTextContent('First alert')
    expect(renderedAlerts[1]).toHaveTextContent('Third alert')
    expect(screen.queryByText('Second alert')).not.toBeInTheDocument()
  })

  it('reverses the stack direction for bottom-positioned alerts', () => {
    render(
      <FloatingAlertStack
        alerts={alerts}
        onClose={jest.fn()}
        position={{ vertical: 'bottom', horizontal: 'right' }}
      />,
    )

    expect(screen.getByTestId('floating-alert-stack')).toHaveStyle({
      flexDirection: 'column-reverse',
    })
  })
})
