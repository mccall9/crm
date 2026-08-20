const PLAYBOOK_TEMPLATES = [
  {
    phase: 'Pre-onboarding',
    title: 'Enviar apresentação formal no grupo',
    offset: 0,
  },
  {
    phase: 'Pre-onboarding',
    title: 'Criar Drive do cliente',
    offset: 0,
  },
  {
    phase: 'Pre-onboarding',
    title: 'Enviar formulário de onboarding',
    offset: 1,
  },
  {
    phase: 'Pre-onboarding',
    title: 'Adicionar squad e alinhar participantes',
    offset: 1,
  },
  {
    phase: 'Onboarding',
    title: 'Agendar reunião de onboarding',
    offset: 2,
  },
  {
    phase: 'Onboarding',
    title: 'Realizar reunião de onboarding',
    offset: 5,
  },
  {
    phase: 'Onboarding',
    title: 'Salvar gravação e transcrição no Drive',
    offset: 5,
  },
  {
    phase: 'Semana 1',
    title: 'Validar acessos e integrações do cliente',
    offset: 6,
  },
  {
    phase: 'Semana 1',
    title: 'Confirmar reunião Hunter x cliente',
    offset: 7,
  },
  {
    phase: 'Semana 2',
    title: 'Criar campanha de indicação',
    offset: 10,
  },
  {
    phase: 'Semana 2',
    title: 'Criar templates de follow-up',
    offset: 11,
  },
  {
    phase: 'Semanas 3–4',
    title: 'Enviar relatório de acompanhamento',
    offset: 15,
  },
  {
    phase: 'Semanas 3–4',
    title: 'Revisar saúde da conta com o cliente',
    offset: 20,
  },
  {
    phase: 'Semana 5',
    title: 'Preparar apresentação consolidada de resultados',
    offset: 25,
  },
  {
    phase: 'Semana 5',
    title: 'Realizar reunião de resultados e aplicar NPS',
    offset: 29,
  },
]

export const CS_PLAYBOOK_PHASES = [
  'Pre-onboarding',
  'Onboarding',
  'Semana 1',
  'Semana 2',
  'Semanas 3–4',
  'Semana 5',
]

function parseDate(value) {
  if (value instanceof Date) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate())
  }

  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [year, month, day] = value.split('-').map(Number)
    return new Date(year, month - 1, day)
  }

  return null
}

function addBusinessDays(date, days) {
  const result = new Date(date)
  let remaining = days

  while (result.getDay() === 0 || result.getDay() === 6) {
    result.setDate(result.getDate() + 1)
  }

  while (remaining > 0) {
    result.setDate(result.getDate() + 1)
    const weekday = result.getDay()
    if (weekday !== 0 && weekday !== 6) remaining -= 1
  }

  return result
}

function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Build the standard CS operational tasks for a client cycle.
 *
 * Dates are business-day offsets from the cycle start, and the returned objects
 * are ready to be used as CRM Task defaults.
 */
export function buildCSPlaybookTasks(startDate, client = {}) {
  const parsedStartDate = parseDate(startDate)
  if (!parsedStartDate) return []

  return PLAYBOOK_TEMPLATES.map((template) => ({
    title: client.name
      ? `${template.title} — ${client.name}`
      : template.title,
    description: `Fase: ${template.phase}`,
    status: 'Backlog',
    priority: 'Medium',
    start_date: formatDate(
      addBusinessDays(parsedStartDate, Math.max(template.offset - 1, 0)),
    ),
    due_date: `${formatDate(addBusinessDays(parsedStartDate, template.offset))} 17:00:00`,
    reference_doctype: client.doctype || undefined,
    reference_docname: client.name || undefined,
    cs_phase: template.phase,
  }))
}

export function getCSPlaybookTemplates() {
  return PLAYBOOK_TEMPLATES.map((template) => ({ ...template }))
}
