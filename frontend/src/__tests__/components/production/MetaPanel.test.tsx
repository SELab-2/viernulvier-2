import { render, screen } from '@testing-library/react'
import MetaPanel from '../../../components/production/MetaPanel'

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ i18n: { language: 'nl' }, t: (_k: string, d: string) => d }),
}))

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

afterEach(() => jest.clearAllMocks())

describe('MetaPanel component', () => {
  it('renders title, tagline, meta rows, and tags', () => {
    render(
      <MetaPanel
        title="Titel"
        tagline="Tag"
        artistName="Artist"
        dateRange="1-31 aug"
        venues="V"
        genres="Drama"
        typeName="Type"
        performerType="group"
        attendanceMode="offline"
        allTags={['tag1', 'tag2']}
      />,
    )

    expect(screen.getByText('Titel')).toBeInTheDocument()
    expect(screen.getByText('Tag')).toBeInTheDocument()
    expect(screen.getByText('Periode')).toBeInTheDocument()
    expect(screen.getByText('Locaties')).toBeInTheDocument()
    expect(screen.getByText('Genre')).toBeInTheDocument()
    expect(screen.getByText('Groep')).toBeInTheDocument()
    expect(screen.getByText('Fysiek')).toBeInTheDocument()
    expect(screen.getByText('tag1')).toBeInTheDocument()
    expect(screen.getByText('tag2')).toBeInTheDocument()
  })

  it('does not render empty fields and no tags section for none', () => {
    render(
      <MetaPanel
        title="Titel"
        tagline=""
        artistName=""
        dateRange=""
        venues=""
        genres=""
        typeName=""
        performerType=""
        attendanceMode=""
        allTags={[]}
      />,
    )

    expect(screen.getByText('Titel')).toBeInTheDocument()
    expect(screen.queryByText('Periode')).not.toBeInTheDocument()
    expect(screen.queryByText('Locaties')).not.toBeInTheDocument()
    expect(screen.queryByText('Genre')).not.toBeInTheDocument()
    expect(screen.queryByText('Type')).not.toBeInTheDocument()
    expect(screen.queryByText('Uitvoering')).not.toBeInTheDocument()
    expect(screen.queryByText('Aanwezigheid')).not.toBeInTheDocument()
  })

  it('renders artistName fallback and solo/online labels', () => {
    render(
      <MetaPanel
        title="Titel"
        tagline=""
        artistName="Artist"
        dateRange=""
        venues=""
        genres=""
        typeName=""
        performerType="solo"
        attendanceMode="online"
        allTags={[]}
      />,
    )

    expect(screen.getByText('Artist')).toBeInTheDocument()
    expect(screen.getByText('Solo')).toBeInTheDocument()
    expect(screen.getByText('Online')).toBeInTheDocument()
  })
})
