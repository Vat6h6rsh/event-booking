import { useState } from 'react'
import { istInput, eventDate, errorDetail } from '../lib/booking'
import { rupeesToPaise } from '../lib/money'
import { updateEvent } from '../lib/api'
import styles from './OrganizerDashboard.module.css'

const categories = ['Music','Movies','Social','Festival','Sports','Food','Tech','Art','Wellness','Comedy','Theater','Other']
export default function EditEventForm({ event, onSaved, onClose }) {
  const initial = { name: event.name, venue: event.venue, event_date: istInput(event.event_date), end_date: istInput(event.end_date), price: (event.price / 100).toFixed(2), total_tickets: String(event.total_tickets), category: event.category, age_rating: event.age_rating, description: event.description || '', image_url: event.image_url || '', banner_url: event.banner_url || '', tags: event.tags || '' }
  const [form, setForm] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  async function submit(e) {
    e.preventDefault(); if (busy) return
    setErr('')
    try {
      const changes = {}
      for (const key of Object.keys(initial)) {
        if (form[key] === initial[key]) continue
        let value = form[key]
        if (key === 'price') value = rupeesToPaise(value)
        else if (key === 'total_tickets') { value = Number(value); if (!Number.isInteger(value) || value < 1) throw new Error('Capacity must be a positive whole number.') }
        else if (key.endsWith('_date')) {
          if (!value && key === 'end_date') value = null
          else { const date = new Date(`${value}:00+05:30`); if (!Number.isFinite(date.getTime())) throw new Error('Enter a valid IST date and time.'); value = date.toISOString() }
        } else value = value.trim()
        if (value !== event[key]) changes[key] = value
      }
      if (!Object.keys(changes).length) { onClose(); return }
      if (changes.event_date && eventDate(changes.event_date) <= new Date()) throw new Error('Choose a future start date and time in IST.')
      const end = 'end_date' in changes ? changes.end_date : event.end_date
      if (end && eventDate(end) <= eventDate(changes.event_date || event.event_date)) throw new Error('End time must be after the start time.')
      setBusy(true)
      const { data } = await updateEvent(event.id, changes)
      onSaved(data)
    } catch (ex) { setErr(errorDetail(ex, ex.message)) }
    finally { setBusy(false) }
  }
  return <form className={styles.form} onSubmit={submit} aria-label={`Edit ${event.name}`}>
    <h2>Edit event</h2><p>Saving changes emails and notifies customers with confirmed bookings.</p>
    <fieldset disabled={busy} className={styles.fields}>
      <div className={styles.grid2}>{Object.keys(initial).map(key => <label key={key} className={styles.field}>
        <span>{({ event_date: 'Start date & time (IST)', end_date: 'End date & time (IST)', price: 'Base price (₹)', total_tickets: 'Total tickets', image_url: 'Image URL', banner_url: 'Banner URL', age_rating: 'Age rating' })[key] || key[0].toUpperCase() + key.slice(1)}</span>
        {key === 'category' || key === 'age_rating' ? <select className="input" value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}>{(key === 'category' ? categories : ['U','UA','A','18+']).map(v => <option key={v}>{v}</option>)}</select> : key === 'description' ? <textarea className="input" rows={3} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} /> : <input className="input" type={key.endsWith('_date') ? 'datetime-local' : ['price','total_tickets'].includes(key) ? 'number' : 'text'} min={key === 'total_tickets' ? 1 : key === 'price' ? 0 : undefined} step={key === 'price' ? '0.01' : undefined} required={['name','venue','event_date','price','total_tickets'].includes(key)} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))} />}
      </label>)}</div>
      {err && <p role="alert" className={styles.error}>{err}</p>}
      <div className={styles.actions}><button className="btn btn-primary" type="submit">{busy ? 'Saving...' : 'Save changes & notify bookers'}</button><button className="btn btn-secondary" type="button" onClick={onClose}>Discard changes</button></div>
    </fieldset>
  </form>
}
