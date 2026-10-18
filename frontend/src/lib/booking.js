export function errorDetail(ex, fallback = 'Something went wrong. Please retry.') {
  const detail = ex.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(e => `${(e.loc || []).filter(x => x !== 'body').join(' → ')}: ${typeof e.msg === 'string' ? e.msg : 'Invalid value'}`).join('; ')
  return fallback
}
// Naive API timestamps are UTC; all customer-facing session times are IST.
export const eventDate = value => new Date(/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : `${value}Z`)
export const formatDate = value => value ? `${eventDate(value).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })} IST` : 'Date unavailable'
export const istDay = value => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' }).format(eventDate(value))
export const istInput = value => value ? new Date(eventDate(value).getTime() + 19800000).toISOString().slice(0, 16) : ''
export const eventCity = (event, venues = []) => (event.venue_details?.city || venues.find(v => v.id === event.venue_id)?.city || event.venue?.split(',').slice(1).pop() || '').trim()
export function inventory(event, tiers = event?.tiers || []) {
  const available = tiers.filter(t => t.available_seats > 0)
  return tiers.length ? { sold: !available.length, price: available.length ? Math.min(...available.map(t => t.price)) : null, available: available.reduce((n, t) => n + t.available_seats, 0) } : { sold: !event?.available_tickets, price: event?.price, available: event?.available_tickets || 0 }
}
export function retryDelay(header) {
  if (header == null) return 1000
  const seconds = Number(header)
  return Math.max(0, Number.isFinite(seconds) ? seconds * 1000 : (Date.parse(header) - Date.now()) || 1000)
}
