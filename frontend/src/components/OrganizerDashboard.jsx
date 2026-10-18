import { formatMoney, rupeesToPaise } from '../lib/money'
import { errorDetail, formatDate } from '../lib/booking'
import { useState, useEffect, useRef } from 'react'
import { getMyEventStats, getMyEvents, createEvent, createTier, getMyVenues, createVenue, uploadImage, getTiers, updateEvent } from '../lib/api'
import { useApp } from '../context/AppContext'
import EditEventForm from './EditEventForm'
import styles from './OrganizerDashboard.module.css'

const TABS = ['My Events', 'Create Event', 'My Venues', 'Add Venue', 'Bookings Overview']

const defaultEvent = {
  name:'', venue:'', event_date:'', total_tickets:'', price:'0',
  category:'Music', event_type:'Music', age_rating:'U', description:'',
  image_url:'', banner_url:'', has_seat_selection: false, tags:'', status:'draft',
}

const defaultVenue = { name:'', address:'', city:'', state:'', capacity:'', description:'', image_url:'', website:'' }

const defaultTier = { name:'', price:'', total_seats:'', color:'#A78BFA', description:'', benefits:'', position:0 }

function Ef({ label, name, value, onChange, type='text', required, placeholder, min }) {
    return (
      <div className={styles.field}>
        <label htmlFor={`organizer-${name}`} className={styles.label}>{label}{required && ' *'}</label>
        <input id={`organizer-${name}`} className="input" type={type} step={name === 'price' ? '0.01' : undefined} name={name} value={value}
          onChange={e => onChange(e.target.value)} required={required}
          placeholder={placeholder} min={min} />
      </div>
    )
  }

export default function OrganizerDashboard() {
  const { user, addToast, setCatalogueVersion } = useApp()
  const [editing, setEditing] = useState(null)
  const [confirmation, setConfirmation] = useState(null)
  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState('')
  const [statsVersion, setStatsVersion] = useState(0)
  useEffect(() => {
    let ignore = false
    setStatsError(''); setStats(null)
    getMyEventStats().then(r => { if (!ignore) setStats(r.data) }).catch(ex => { if (!ignore) setStatsError(errorDetail(ex, 'Could not load booking figures.')) })
    return () => { ignore = true }
  }, [statsVersion])
  function saved(data) {
    setMyEvents(list => list.map(ev => ev.id === data.id ? data : ev))
    setCatalogueVersion(v => v + 1); setEditing(null); setConfirmation(null)
    const count = stats?.find(x => x.event_id === data.id)?.confirmed_bookings
    addToast(count === 0 ? 'Event updated - No bookings yet, nobody to notify' : count == null ? 'Event updated - Customers who booked will be notified' : `Event updated - ${count} customer(s) who booked will be notified`)
    setStatsVersion(v => v + 1)
  }
  async function changeStatus() {
    if (guard.current) return
    guard.current = true; setBusy(true); setFormError('')
    try { const { data } = await updateEvent(confirmation.event.id, { status: confirmation.status }); saved(data) }
    catch (ex) { setFormError(errorDetail(ex)) }
    finally { guard.current = false; setBusy(false) }
  }
  const totals = stats?.reduce((sum, row) => { for (const key of Object.keys(sum)) sum[key] += row[key]; return sum }, { tickets_sold: 0, gross_paise: 0, confirmed_bookings: 0, cancelled_bookings: 0 })
  const [tab, setTab] = useState(0)
  const [myEvents, setMyEvents] = useState([])
  const [myVenues, setMyVenues] = useState([])
  const [eventForm, setEventForm] = useState(defaultEvent)
  const [tiers, setTiers]   = useState([{ ...defaultTier }])
  const [venueForm, setVenueForm] = useState(defaultVenue)
  const [busy, setBusy] = useState(false)
  const [setup, setSetupState] = useState(() => { try { return JSON.parse(sessionStorage.getItem(`jtickets_draft_setup_${user?.id}`) || 'null') } catch { return null } })
  const setupRef = useRef(setup)
  const guard = useRef(false)
  const [formError, setFormError] = useState('')
  const [myEventsError, setMyEventsError] = useState('')
  function saveSetup(value) { setupRef.current = value; setSetupState(value); if (value) sessionStorage.setItem(`jtickets_draft_setup_${user?.id}`, JSON.stringify(value)); else sessionStorage.removeItem(`jtickets_draft_setup_${user?.id}`) }
  const [uploading, setUploading] = useState(false)

  useEffect(() => { getMyEvents().then(r => setMyEvents(r.data)).catch(ex => setMyEventsError(errorDetail(ex))) }, [])
  useEffect(() => { getMyVenues().then(r => setMyVenues(r.data)).catch(() => {}) }, [])

  async function handleImageUpload(e, field, setForm) {
    const file = e.target.files[0]; if (!file) return
    setUploading(true)
    try {
      const res = await uploadImage(file)
      setForm(f => ({ ...f, [field]: res.data.url }))
      addToast('Image uploaded to R2!')
    } catch {
      addToast('Upload failed. Check R2 configuration.', 'error')
    } finally { setUploading(false) }
  }

  async function checkDrafts() {
    if (guard.current) return
    guard.current = true; setBusy(true); setFormError('')
    try { const { data } = await getMyEvents(); setMyEvents(data); setMyEventsError(''); setTab(0) }
    catch(ex) { setFormError(errorDetail(ex)) }
    finally { guard.current = false; setBusy(false) }
  }
  function editPendingTier(index, field, value) {
    const job = setupRef.current
    if (!job || index < job.done || job.uncertainTier || guard.current) return
    try {
      const parsed = field === 'price' ? rupeesToPaise(value) : field === 'total_seats' ? Number(value) : value.trim()
      if (field === 'total_seats' && (!Number.isInteger(parsed) || parsed < 1)) throw new Error('Tier capacity must be a positive whole number.')
      saveSetup({ ...job, tiers: job.tiers.map((t, i) => i === index ? { ...t, [field]: parsed } : t) })
      setFormError('')
    } catch(ex) { setFormError(ex.message) }
  }
  async function completeTiers() {
    let job = setupRef.current
    if (!job?.eventId) return
    for (let i = job.done; i < job.tiers.length; i++) {
      // Read before writing. An uncertain POST must be reconciled before another write.
      const { data: existing } = await getTiers(job.eventId)
      const wanted = job.tiers[i]
      if (!wanted.name.trim()) throw new Error('A tier name is required.')
      const matches = existing.filter(t => t.name === wanted.name && t.price === wanted.price && t.total_seats === wanted.total_seats)
      if (matches.length === 1) { job = { ...job, done: i + 1, uncertainTier: false }; saveSetup(job); continue }
      if (job.uncertainTier) throw new Error('The last tier request has an uncertain outcome. Check saved tiers again before continuing. No duplicate tier has been sent.')
      saveSetup({ ...job, uncertainTier: true })
      try { await createTier(job.eventId, wanted) }
      catch(ex) { if (ex.response && ex.response.status < 500) saveSetup({ ...job, uncertainTier: false }); throw ex }
      job = { ...job, done: i + 1, uncertainTier: false }; saveSetup(job)
    }
    saveSetup({ ...job, ready: true })
    setFormError('')
  }
  async function handleCreateEvent(e) {
    e.preventDefault()
    if (guard.current || setupRef.current?.uncertainEvent) return
    guard.current = true; setBusy(true); setFormError('')
    try {
      if (!setupRef.current) {
        const configured = tiers.filter(t => t.name || t.price || t.total_seats).map(t => {
          if (!t.name.trim() || !Number.isInteger(Number(t.total_seats)) || Number(t.total_seats) < 1) throw new Error('Every configured tier needs a name, price and positive whole-ticket capacity.')
          return { ...t, name: t.name.trim(), price: rupeesToPaise(t.price), total_seats: Number(t.total_seats) }
        })
        const localTime = new Date(`${eventForm.event_date}:00+05:30`)
        if (!Number.isFinite(localTime.getTime()) || localTime <= new Date()) throw new Error('Choose a future date and time in IST.')
        const payload = { ...eventForm, event_date: localTime.toISOString(), total_tickets: Number(eventForm.total_tickets), price: rupeesToPaise(eventForm.price || '0'), status: 'draft', has_seat_selection: false }
        if (!Number.isInteger(payload.total_tickets) || payload.total_tickets < 1) throw new Error('Ticket capacity must be a positive whole number.')
        const pending = { payload, tiers: configured, done: 0, uncertainEvent: true }
        saveSetup(pending)
        let result
        try { result = await createEvent(payload) }
        catch(ex) { if (ex.response && ex.response.status < 500) saveSetup(null); throw ex }
        saveSetup({ ...pending, eventId: result.data.id, uncertainEvent: false })
        setMyEvents(list => [result.data, ...list])
      }
      await completeTiers()
    } catch(ex) { setFormError(errorDetail(ex, ex.message || 'Setup failed. Your draft and remaining tier setup have been retained.')) }
    finally { guard.current = false; setBusy(false) }
  }
  async function publish() {
    if (guard.current || !setupRef.current?.ready) return
    guard.current = true; setBusy(true); setFormError('')
    try {
      const { data } = await updateEvent(setupRef.current.eventId, { status: 'published' })
      setMyEvents(list => [data, ...list.filter(x => x.id !== data.id)])
      saveSetup(null); setEventForm(defaultEvent); setTiers([{ ...defaultTier }]); setTab(0)
      setCatalogueVersion(v => v + 1); setStatsVersion(v => v + 1)
      addToast('Event published with all ticket tiers configured.')
    } catch(ex) { setFormError(errorDetail(ex, 'Could not confirm publication. The saved event can be checked and publication retried safely.')) }
    finally { guard.current = false; setBusy(false) }
  }
  async function handleCreateVenue(e) {
    e.preventDefault(); setBusy(true)
    try {
      const v = await createVenue({ ...venueForm, capacity: parseInt(venueForm.capacity) })
      addToast(`Venue "${v.data.name}" added!`)
      setVenueForm(defaultVenue); setMyVenues(p => [v.data, ...p]); setTab(2)
    } catch (ex) {
      addToast(errorDetail(ex, 'Create failed'), 'error')
    } finally { setBusy(false) }
  }


  return (
    <div className={styles.dash}>
      <div className={styles.header}>
        <h1 className={styles.title}>Organizer Dashboard</h1>
        <p className={styles.sub}>Welcome back, <strong>{user?.full_name || user?.email}</strong></p>
      </div>
      {formError && <p role="alert" className={styles.error}>{formError}</p>}
      {setup && <section className={styles.recovery} aria-label="Saved event setup"><h2>Saved draft setup</h2><p>{setup.eventId ? `Draft #${setup.eventId}` : 'Creation outcome uncertain'} · {setup.payload.name}. {setup.done}/{setup.tiers.length} tiers confirmed.</p>
        <p>{formatDate(setup.payload.event_date)} · Base {formatMoney(setup.payload.price)}</p>
        <ul>{setup.tiers.map((t, i) => <li key={i}>{t.name} · {formatMoney(t.price)} · {t.total_seats} tickets · {i < setup.done ? 'Saved' : 'Pending'}
          {i >= setup.done && !setup.uncertainTier && !setup.ready && <div className={styles.pendingTier}>
            <label>Name<input className="input" disabled={busy} defaultValue={t.name} onBlur={e => editPendingTier(i, 'name', e.target.value)} /></label>
            <label>Price (₹)<input className="input" disabled={busy} type="number" min="0" step="0.01" defaultValue={(t.price / 100).toFixed(2)} onBlur={e => editPendingTier(i, 'price', e.target.value)} /></label>
            <label>Capacity<input className="input" disabled={busy} type="number" min="1" step="1" defaultValue={t.total_seats} onBlur={e => editPendingTier(i, 'total_seats', e.target.value)} /></label>
          </div>}
        </li>)}</ul>
        {setup.uncertainEvent ? <><p>Check your saved drafts and explicitly select the matching event below before resuming. A second event will not be created.</p><button className="btn btn-secondary" disabled={busy} onClick={checkDrafts}>Check saved drafts</button></> : setup.ready ? <><p>Review the saved details and ticket tiers above. Publish when ready.</p><button className="btn btn-primary" disabled={busy} onClick={publish}>{busy ? 'Publishing...' : 'Publish event'}</button></> : <button className="btn btn-primary" disabled={busy} onClick={handleCreateEvent}>{busy ? 'Checking setup...' : 'Retry remaining tier setup'}</button>}
      </section>}
      <div className={styles.tabs}>
        {TABS.map((t, i) => (
          <button key={t} className={`${styles.tab} ${tab === i ? styles.tabActive : ''}`} onClick={() => setTab(i)}>{t}</button>
        ))}
      </div>

      {statsError && <p role="alert">{statsError} <button className="btn btn-secondary" onClick={() => setStatsVersion(v => v + 1)}>Retry booking figures</button></p>}
      {editing && <EditEventForm key={editing.id} event={editing} onSaved={saved} onClose={() => setEditing(null)} />}
      {confirmation && <section className={styles.recovery} aria-label="Confirm event status change"><h2>{confirmation.status === 'cancelled' ? 'Cancel event' : confirmation.status === 'draft' ? 'Unpublish event' : 'Publish event'}: {confirmation.event.name}?</h2><p>Confirmed bookers will be notified. {confirmation.status === 'cancelled' && 'The event will no longer accept bookings. No payment refund is issued.'}</p><div className={styles.actions}><button className="btn btn-primary" disabled={busy} onClick={changeStatus}>Confirm change</button><button className="btn btn-secondary" disabled={busy} onClick={() => setConfirmation(null)}>Keep current status</button></div></section>}
      {/* My Events */}
      {tab === 0 && (
        <div className={styles.list}>
          {myEventsError && <p role="alert">{myEventsError}<button className="btn btn-secondary" onClick={checkDrafts}>Retry events</button></p>}
          {myEvents.length === 0 && <p className={styles.empty}>No events yet. Create your first event!</p>}
          {myEvents.map(ev => (
            <div key={ev.id} className={styles.evCard}>
              <div className={styles.evImg}>
                {ev.image_url && <img src={ev.image_url} alt={ev.name} />}
              </div>
              <div className={styles.evInfo}>
                <h3>{ev.name}</h3>
                {setup?.uncertainEvent && ev.status === 'draft' && ev.name === setup.payload.name && <button className="btn btn-secondary" disabled={busy} onClick={() => { saveSetup({ ...setup, eventId: ev.id, uncertainEvent: false }); setTab(1) }}>Use this saved draft #{ev.id}</button>}
                <div className={styles.evMeta}>
                  <span>{ev.venue}</span>
                  <span>📅 {formatDate(ev.event_date)}</span>
                  <span className={`badge badge-${ev.category === 'Music' ? 'music' : ev.category === 'Movies' ? 'movies' : 'other'}`}>{ev.category}</span>
                  <span className={ev.status === 'published' ? styles.published : styles.draft}>{ev.status}</span>
                </div>
                <div className={styles.evStats}>
                  <span>🎟️ {ev.available_tickets}/{ev.total_tickets} left</span>
                  <span>💰 {formatMoney(ev.price)}</span>
                  <span>🔞 {ev.age_rating}</span>
                </div>
                <div className={styles.sellThrough}>{stats?.find(x => x.event_id === ev.id) ? (() => { const row = stats.find(x => x.event_id === ev.id); const percent = ev.total_tickets ? Math.round(row.tickets_sold / ev.total_tickets * 100) : 0; return <><span>{row.tickets_sold} sold | {percent}% sell-through | {row.confirmed_bookings} confirmed bookings</span><progress max="100" value={percent} aria-label={`${ev.name} sell-through`} /></> })() : <span>{statsError ? 'Booking figures unavailable' : 'Loading booking figures...'}</span>}</div>
                <div className={styles.actions}><button className="btn btn-secondary btn-sm" disabled={busy} onClick={() => { setEditing(ev); setConfirmation(null) }}>Edit</button>{ev.status !== 'cancelled' && <><button className="btn btn-secondary btn-sm" disabled={busy} onClick={() => setConfirmation({ event: ev, status: ev.status === 'published' ? 'draft' : 'published' })}>{ev.status === 'published' ? 'Unpublish' : 'Publish'}</button><button className="btn btn-secondary btn-sm" disabled={busy} onClick={() => setConfirmation({ event: ev, status: 'cancelled' })}>Cancel event</button></>}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Event */}
      {tab === 1 && (
        <form className={styles.form} onSubmit={handleCreateEvent}>
          <h2 className={styles.formTitle}>Create a draft</h2>
          <p>Save a draft and its ticket tiers, review, then explicitly publish.</p>
          <fieldset disabled={busy || uploading || !!setup} className={styles.fields}>
          <div className={styles.grid2}>
            <Ef label="Event Name" name="name" value={eventForm.name} onChange={v => setEventForm(f => ({...f, name:v}))} required />
            <Ef label="Venue (text)" name="venue" value={eventForm.venue} onChange={v => setEventForm(f => ({...f, venue:v}))} required />
          </div>
          <div className={styles.grid3}>
            <Ef label="Date & Time (IST)" name="event_date" type="datetime-local" value={eventForm.event_date} onChange={v => setEventForm(f => ({...f, event_date:v}))} required />
            <div className={styles.field}>
              <label htmlFor="organizer-category" className={styles.label}>Category</label>
              <select id="organizer-category" className="input" value={eventForm.category} onChange={e => setEventForm(f => ({...f, category:e.target.value, event_type:e.target.value}))}>
                {['Music','Movies','Social','Festival','Sports','Food','Tech','Art','Wellness','Comedy','Theater','Other'].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className={styles.field}>
              <label htmlFor="organizer-age-rating" className={styles.label}>Age Rating</label>
              <select id="organizer-age-rating" className="input" value={eventForm.age_rating} onChange={e => setEventForm(f => ({...f, age_rating:e.target.value}))}>
                {['U','UA','A','18+'].map(r => <option key={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <div className={styles.grid2}>
            <Ef label="Total Tickets" name="total_tickets" type="number" min="1" value={eventForm.total_tickets} onChange={v => setEventForm(f => ({...f, total_tickets:v}))} required />
            <Ef label="Base Price (₹)" name="price" type="number" min="0" value={eventForm.price} onChange={v => setEventForm(f => ({...f, price:v}))} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Description</label>
            <textarea className="input" rows={3} value={eventForm.description} onChange={e => setEventForm(f => ({...f, description:e.target.value}))} placeholder="Describe your event…" />
          </div>
          <div className={styles.grid2}>
            <div className={styles.field}>
              <label className={styles.label}>Event Image URL</label>
              <input className="input" value={eventForm.image_url} onChange={e => setEventForm(f => ({...f, image_url:e.target.value}))} placeholder="https://..." />
              <label className={styles.uploadBtn}>
                {uploading ? 'Uploading…' : 'Or upload image'}
                <input type="file" accept="image/*" style={{display:'none'}} onChange={e => handleImageUpload(e, 'image_url', setEventForm)} />
              </label>
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Banner URL</label>
              <input className="input" value={eventForm.banner_url} onChange={e => setEventForm(f => ({...f, banner_url:e.target.value}))} placeholder="https://..." />
              <label className={styles.uploadBtn}>
                {uploading ? 'Uploading…' : 'Or upload banner'}
                <input type="file" accept="image/*" style={{display:'none'}} onChange={e => handleImageUpload(e, 'banner_url', setEventForm)} />
              </label>
            </div>
          </div>
          <div className={styles.checkRow}>
            <label className={styles.checkLabel}>
              <input type="checkbox" disabled checked={false}
                onChange={e => setEventForm(f => ({...f, has_seat_selection:e.target.checked}))} />
              Reserved-seat selection unavailable; general admission / tier booking only
            </label>
          </div>
          <Ef label="Tags (comma-separated)" name="tags" value={eventForm.tags} onChange={v => setEventForm(f => ({...f, tags:v}))} placeholder="rock, outdoor, family-friendly" />

          {/* Ticket Tiers */}
          <div className={styles.tiersSection}>
            <div className={styles.tiersHeader}>
              <h3 className={styles.tiersTitle}>Ticket Tiers (optional)</h3>
              <button type="button" className="btn btn-sm" onClick={() => setTiers(t => [...t, {...defaultTier, position:t.length}])}>+ Add tier</button>
            </div>
            {tiers.map((t, i) => (
              <div key={i} className={styles.tierRow}>
                <input className="input" aria-label={`Tier ${i + 1} name`} placeholder="Tier name (e.g. VIP)" value={t.name} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, name:e.target.value} : x))} />
                <input className="input" type="number" aria-label={`Tier ${i + 1} price in rupees`} step="0.01" placeholder="Price (₹)" min="0" value={t.price} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, price:e.target.value} : x))} />
                <input className="input" type="number" aria-label={`Tier ${i + 1} capacity`} placeholder="Seats" min="1" value={t.total_seats} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, total_seats:e.target.value} : x))} />
                <input className={styles.colorPicker} type="color" value={t.color} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, color:e.target.value} : x))} title="Tier colour" />
                <button type="button" aria-label={`Remove tier ${i + 1}`} className={styles.removeTier} onClick={() => setTiers(ts => ts.filter((_,j) => j!==i))}>✕</button>
              </div>
            ))}
          </div>

          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Saving draft…' : 'Save draft and ticket tiers'}</button>
          </fieldset>
        </form>
      )}

      {/* My Venues */}
      {tab === 2 && (
        <div className={styles.list}>
          {myVenues.length === 0 && <p className={styles.empty}>No venues yet. Add your first venue!</p>}
          {myVenues.map(v => (
            <div key={v.id} className={styles.venueCard}>
              {v.image_url && <img src={v.image_url} alt={v.name} className={styles.venueImg} />}
              <div>
                <h3>{v.name}</h3>
                <p className={styles.venueMeta}>{v.address}, {v.city} · Capacity: {v.capacity.toLocaleString()}</p>
                {v.description && <p className={styles.venueDesc}>{v.description}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Venue */}
      {tab === 3 && (
        <form className={styles.form} onSubmit={handleCreateVenue}>
          <h2 className={styles.formTitle}>Onboard a Venue</h2>
          <div className={styles.grid2}>
            <Ef label="Venue Name" name="name" value={venueForm.name} onChange={v => setVenueForm(f => ({...f, name:v}))} required />
            <Ef label="City" name="city" value={venueForm.city} onChange={v => setVenueForm(f => ({...f, city:v}))} required />
          </div>
          <Ef label="Address" name="address" value={venueForm.address} onChange={v => setVenueForm(f => ({...f, address:v}))} required />
          <div className={styles.grid2}>
            <Ef label="State" name="state" value={venueForm.state} onChange={v => setVenueForm(f => ({...f, state:v}))} />
            <Ef label="Capacity" name="capacity" type="number" min="1" value={venueForm.capacity} onChange={v => setVenueForm(f => ({...f, capacity:v}))} required />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Description</label>
            <textarea className="input" rows={3} value={venueForm.description} onChange={e => setVenueForm(f => ({...f, description:e.target.value}))} placeholder="Describe the venue…" />
          </div>
          <div className={styles.grid2}>
            <div className={styles.field}>
              <label className={styles.label}>Venue Image URL</label>
              <input className="input" value={venueForm.image_url} onChange={e => setVenueForm(f => ({...f, image_url:e.target.value}))} placeholder="https://..." />
              <label className={styles.uploadBtn}>
                {uploading ? 'Uploading…' : 'Or upload image'}
                <input type="file" accept="image/*" style={{display:'none'}} onChange={e => handleImageUpload(e, 'image_url', setVenueForm)} />
              </label>
            </div>
            <Ef label="Website" name="website" value={venueForm.website} onChange={v => setVenueForm(f => ({...f, website:v}))} placeholder="https://venue.com" />
          </div>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Adding…' : 'Add Venue'}</button>
        </form>
      )}

      {/* Bookings overview — quick stats */}
      {tab === 4 && (totals ? <div className={styles.statsGrid}>
        {[['Tickets sold', totals.tickets_sold], ['Booked value', formatMoney(totals.gross_paise)], ['Confirmed bookings', totals.confirmed_bookings], ['Cancellations', totals.cancelled_bookings]].map(([label, value]) => <div key={label} className={styles.statCard}><span className={styles.statNum}>{value}</span><span>{label}</span></div>)}
      </div> : !statsError && <p role="status">Loading booking figures...</p>)}
    </div>
  )
}
