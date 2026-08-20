import {
  buildCSMeetingSubject,
  validateCSMeetingWindow,
} from '@/utils/csCalendar'
import { describe, expect, it } from 'vitest'

describe('CS calendar rules', () => {
  it('builds the operational meeting subject', () => {
    expect(
      buildCSMeetingSubject('Reunião de onboarding', 'Dra. Camila', [
        'CS',
        'EST',
        'GP',
      ]),
    ).toBe('ATL | REUNIÃO DE ONBOARDING [CS+EST+GP] [DRA. CAMILA]')
  })

  it('rejects an empty client name', () => {
    expect(() => buildCSMeetingSubject('Onboarding', '')).toThrow(
      'A client name is required',
    )
  })

  it('accepts a weekday meeting during business hours', () => {
    expect(
      validateCSMeetingWindow(
        '2026-08-17T09:00:00',
        '2026-08-17T10:30:00',
      ),
    ).toEqual({ valid: true, reason: null })
  })

  it('rejects weekends and times outside business hours', () => {
    expect(
      validateCSMeetingWindow(
        '2026-08-15T10:00:00',
        '2026-08-15T11:00:00',
      ).reason,
    ).toBe('must_be_business_day')
    expect(
      validateCSMeetingWindow(
        '2026-08-17T08:30:00',
        '2026-08-17T09:30:00',
      ).reason,
    ).toBe('outside_business_hours')
  })

  it('rejects meetings that cross midnight or end before they start', () => {
    expect(
      validateCSMeetingWindow(
        '2026-08-17T17:00:00',
        '2026-08-18T18:00:00',
      ).reason,
    ).toBe('must_be_same_business_day')
    expect(
      validateCSMeetingWindow(
        '2026-08-17T11:00:00',
        '2026-08-17T10:00:00',
      ).reason,
    ).toBe('end_before_start')
  })
})
