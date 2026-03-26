import type { Hall } from '../../types/Halls'
import getLocationName from '../../utils/locations'

describe('getLocationName', () => {
  it('returns empty string for undefined hall', () => {
    expect(getLocationName(undefined, 'nl')).toBe('')
  })

  it('returns empty string for null hall', () => {
    expect(getLocationName(null, 'nl')).toBe('')
  })

  it('prefers translated space location name when available', () => {
    const hall: Hall = {
      id: 1,
      space: {
        id: 1,
        location: {
          id: 1,
          street: null,
          number: null,
          postal_code: null,
          city: null,
          country: 'BE',
          phone_1: null,
          phone_2: null,
          is_own_location: true,
          name: { nl: 'Campus', en: 'Campus EN' },
          display_name: null,
        },
        name: { nl: 'Zaaltje A' },
        display_name: null,
        halls: [],
      },
      seat_selection: false,
      open_seating: true,
      name: { nl: 'Zaal 1' },
      display_name: null,
      remark: null,
    }
    expect(getLocationName(hall, 'nl')).toBe('Campus')
  })

  it('falls back to space name when location name has no translation for language', () => {
    const hall: Hall = {
      id: 1,
      space: {
        id: 1,
        location: {
          id: 1,
          street: null,
          number: null,
          postal_code: null,
          city: null,
          country: 'BE',
          phone_1: null,
          phone_2: null,
          is_own_location: true,
          name: { en: 'Only EN' },
          display_name: null,
        },
        name: { nl: 'Grote zaal' },
        display_name: null,
        halls: [],
      },
      seat_selection: false,
      open_seating: true,
      name: { nl: 'Zaal 1' },
      display_name: null,
      remark: null,
    }
    expect(getLocationName(hall, 'nl')).toBe('Grote zaal')
  })

  it('falls back to hall name when space is null', () => {
    const hall: Hall = {
      id: 1,
      space: null,
      seat_selection: false,
      open_seating: true,
      name: { nl: 'Kleine zaal' },
      display_name: null,
      remark: null,
    }
    expect(getLocationName(hall, 'nl')).toBe('Kleine zaal')
  })

  it('falls back to hall name when space exists but location and space names are empty', () => {
    const hall: Hall = {
      id: 1,
      space: {
        id: 1,
        location: {
          id: 1,
          street: null,
          number: null,
          postal_code: null,
          city: null,
          country: 'BE',
          phone_1: null,
          phone_2: null,
          is_own_location: true,
          name: null,
          display_name: null,
        },
        name: null,
        display_name: null,
        halls: [],
      },
      seat_selection: false,
      open_seating: true,
      name: { nl: 'Reserve naam' },
      display_name: null,
      remark: null,
    }
    expect(getLocationName(hall, 'nl')).toBe('Reserve naam')
  })

  it('returns empty string when nothing is translatable', () => {
    const hall: Hall = {
      id: 1,
      space: {
        id: 1,
        location: {
          id: 1,
          street: null,
          number: null,
          postal_code: null,
          city: null,
          country: 'BE',
          phone_1: null,
          phone_2: null,
          is_own_location: true,
          name: null,
          display_name: null,
        },
        name: null,
        display_name: null,
        halls: [],
      },
      seat_selection: false,
      open_seating: true,
      name: null,
      display_name: null,
      remark: null,
    }
    expect(getLocationName(hall, 'nl')).toBe('')
  })

  it('uses the space name when the location has no name but the space does', () => {
    const hall: Hall = {
      id: 1,
      space: {
        id: 1,
        location: {
          id: 1,
          street: null,
          number: null,
          postal_code: null,
          city: null,
          country: 'BE',
          phone_1: null,
          phone_2: null,
          is_own_location: true,
          name: null,
          display_name: null,
        },
        name: { nl: 'Studio B' },
        display_name: null,
        halls: [],
      },
      seat_selection: false,
      open_seating: true,
      name: { nl: 'Zaal' },
      display_name: null,
      remark: null,
    }
    expect(getLocationName(hall, 'nl')).toBe('Studio B')
  })
})
