import { isActuallyUpcoming } from '../src/app/api/matches/upcoming/route'

describe('isActuallyUpcoming', () => {
  const now = new Date('2026-09-24T10:00:00.000Z').getTime()

  it('rejects fixtures whose kickoff is already past', () => {
    expect(isActuallyUpcoming({
      kickoff: '2026-09-24T09:59:00.000Z',
      status: 'NS',
    }, now)).toBe(false)
  })

  it('rejects terminal fixtures even with a future timestamp', () => {
    expect(isActuallyUpcoming({
      kickoff: '2026-09-24T12:00:00.000Z',
      status: 'FT',
    }, now)).toBe(false)
  })

  it('accepts a future non-terminal fixture', () => {
    expect(isActuallyUpcoming({
      kickoff: '2026-09-24T12:00:00.000Z',
      status: 'NS',
    }, now)).toBe(true)
  })
})
