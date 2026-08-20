import {
  buildCSPlaybookTasks,
  CS_PLAYBOOK_PHASES,
  getCSPlaybookTemplates,
} from '@/utils/csPlaybook'
import { describe, expect, it } from 'vitest'

describe('CS playbook', () => {
  it('returns the complete five-week task sequence', () => {
    const tasks = buildCSPlaybookTasks('2026-08-03', {
      doctype: 'CRM Organization',
      name: 'Atlas Clinic',
    })

    expect(tasks).toHaveLength(15)
    expect(tasks[0]).toMatchObject({
      title: 'Enviar apresentação formal no grupo — Atlas Clinic',
      status: 'Backlog',
      reference_doctype: 'CRM Organization',
      reference_docname: 'Atlas Clinic',
      cs_phase: 'Pre-onboarding',
    })
    expect(tasks.at(-1).cs_phase).toBe('Semana 5')
  })

  it('skips weekends when calculating due dates', () => {
    const tasks = buildCSPlaybookTasks('2026-08-07')

    expect(tasks[0].due_date).toBe('2026-08-07 17:00:00')
    expect(tasks[2].due_date).toBe('2026-08-10 17:00:00')
  })

  it('normalizes a weekend cycle start to the next business day', () => {
    const tasks = buildCSPlaybookTasks('2026-08-08')

    expect(tasks[0].due_date).toBe('2026-08-10 17:00:00')
  })

  it('returns an empty list for an invalid start date', () => {
    expect(buildCSPlaybookTasks('not-a-date')).toEqual([])
    expect(buildCSPlaybookTasks(null)).toEqual([])
  })

  it('does not expose mutable template objects', () => {
    const templates = getCSPlaybookTemplates()
    templates[0].title = 'Changed'

    expect(getCSPlaybookTemplates()[0].title).not.toBe('Changed')
    expect(CS_PLAYBOOK_PHASES).toContain('Semana 5')
  })
})
