const BUSINESS_START_HOUR = 9
const BUSINESS_END_HOUR = 18

export function buildCSMeetingSubject(type, clientName, participants = []) {
  const participantCodes = participants.length
    ? participants.join('+')
    : 'CS'
  const normalizedClient = String(clientName || '').trim().toUpperCase()

  if (!normalizedClient) {
    throw new Error('A client name is required to create a meeting subject.')
  }

  return `ATL | ${String(type || 'REUNIÃO').trim().toUpperCase()} [${participantCodes}] [${normalizedClient}]`
}

export function validateCSMeetingWindow(start, end) {
  const startDate = parseDate(start)
  const endDate = parseDate(end)

  if (!startDate || !endDate) {
    return { valid: false, reason: 'invalid_datetime' }
  }

  if (endDate <= startDate) {
    return { valid: false, reason: 'end_before_start' }
  }

  if (startDate.toDateString() !== endDate.toDateString()) {
    return { valid: false, reason: 'must_be_same_business_day' }
  }

  const weekday = startDate.getDay()
  if (weekday === 0 || weekday === 6) {
    return { valid: false, reason: 'must_be_business_day' }
  }

  const startsAt = startDate.getHours() + startDate.getMinutes() / 60
  const endsAt = endDate.getHours() + endDate.getMinutes() / 60
  if (
    startsAt < BUSINESS_START_HOUR ||
    endsAt > BUSINESS_END_HOUR ||
    endsAt <= startsAt
  ) {
    return { valid: false, reason: 'outside_business_hours' }
  }

  return { valid: true, reason: null }
}

function parseDate(value) {
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value
  }

  if (typeof value !== 'string') return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}
