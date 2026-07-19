import { useState, useEffect } from 'react'
import { getMyEvents, createEvent, createTier, getMyVenues, createVenue, uploadImage, myBookings } from '../lib/api'
import { useApp } from '../context/AppContext'
import styles from './OrganizerDashboard.module.css'

const TABS = ['My Events', 'Create Event', 'My Venues', 'Add Venue', 'Bookings Overview']

const defaultEvent = {
  name:'', venue:'', event_date:'', total_tickets:'', price:'0',
  category:'Music', event_type:'Music', age_rating:'U', description:'',
  image_url:'', banner_url:'', has_seat_selection: false, tags:'', status:'published',
}

const defaultVenue = { name:'', address:'', city:'', state:'', capacity:'', description:'', image_url:'', website:'' }

const defaultTier = { name:'', price:'', total_seats:'', color:'#A78BFA', description:'', benefits:'', position:0 }

export default function OrganizerDashboard() {
  const { user, addToast } = useApp()
  const [tab, setTab] = useState(0)
  const [myEvents, setMyEvents] = useState([])
  const [myVenues, setMyVenues] = useState([])
  const [eventForm, setEventForm] = useState(defaultEvent)
  const [tiers, setTiers]   = useState([{ ...defaultTier }])
  const [venueForm, setVenueForm] = useState(defaultVenue)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => { getMyEvents().then(r => setMyEvents(r.data)).catch(() => {}) }, [])
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

  async function handleCreateEvent(e) {
    e.preventDefault(); setBusy(true)
    try {
      const ev = await createEvent({
        ...eventForm,
        total_tickets: parseInt(eventForm.total_tickets),
        price: parseInt(eventForm.price || 0),
      })
      for (const t of tiers.filter(x => x.name && x.price && x.total_seats)) {
        await createTier(ev.data.id, { ...t, price: parseInt(t.price), total_seats: parseInt(t.total_seats) })
      }
      addToast(`Event "${ev.data.name}" created!`)
      setEventForm(defaultEvent); setTiers([{ ...defaultTier }])
      setMyEvents(p => [ev.data, ...p]); setTab(0)
    } catch (ex) {
      addToast(ex.response?.data?.detail || 'Create failed', 'error')
    } finally { setBusy(false) }
  }

  async function handleCreateVenue(e) {
    e.preventDefault(); setBusy(true)
    try {
      const v = await createVenue({ ...venueForm, capacity: parseInt(venueForm.capacity) })
      addToast(`Venue "${v.data.name}" added!`)
      setVenueForm(defaultVenue); setMyVenues(p => [v.data, ...p]); setTab(2)
    } catch (ex) {
      addToast(ex.response?.data?.detail || 'Create failed', 'error')
    } finally { setBusy(false) }
  }

  function Ef({ label, name, value, onChange, type='text', required, placeholder, min }) {
    return (
      <div className={styles.field}>
        <label className={styles.label}>{label}{required && ' *'}</label>
        <input className="input" type={type} name={name} value={value}
          onChange={e => onChange(e.target.value)} required={required}
          placeholder={placeholder} min={min} />
      </div>
    )
  }

  return (
    <div className={styles.dash}>
      <div className={styles.header}>
        <h1 className={styles.title}>Organizer Dashboard</h1>
        <p className={styles.sub}>Welcome back, <strong>{user?.full_name || user?.email}</strong></p>
      </div>
      <div className={styles.tabs}>
        {TABS.map((t, i) => (
          <button key={t} className={`${styles.tab} ${tab === i ? styles.tabActive : ''}`} onClick={() => setTab(i)}>{t}</button>
        ))}
      </div>

      {/* My Events */}
      {tab === 0 && (
        <div className={styles.list}>
          {myEvents.length === 0 && <p className={styles.empty}>No events yet. Create your first event!</p>}
          {myEvents.map(ev => (
            <div key={ev.id} className={styles.evCard}>
              <div className={styles.evImg}>
                {ev.image_url && <img src={ev.image_url} alt={ev.name} />}
              </div>
              <div className={styles.evInfo}>
                <h3>{ev.name}</h3>
                <div className={styles.evMeta}>
                  <span>{ev.venue}</span>
                  <span>📅 {new Date(ev.event_date).toLocaleDateString('en-IN')}</span>
                  <span className={`badge badge-${ev.category === 'Music' ? 'music' : ev.category === 'Movies' ? 'movies' : 'other'}`}>{ev.category}</span>
                  <span className={ev.status === 'published' ? styles.published : styles.draft}>{ev.status}</span>
                </div>
                <div className={styles.evStats}>
                  <span>🎟️ {ev.available_tickets}/{ev.total_tickets} left</span>
                  <span>💰 ₹{ev.price.toLocaleString('en-IN')}</span>
                  <span>🔞 {ev.age_rating}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Event */}
      {tab === 1 && (
        <form className={styles.form} onSubmit={handleCreateEvent}>
          <h2 className={styles.formTitle}>Create New Event</h2>
          <div className={styles.grid2}>
            <Ef label="Event Name" name="name" value={eventForm.name} onChange={v => setEventForm(f => ({...f, name:v}))} required />
            <Ef label="Venue (text)" name="venue" value={eventForm.venue} onChange={v => setEventForm(f => ({...f, venue:v}))} required />
          </div>
          <div className={styles.grid3}>
            <Ef label="Date & Time" name="event_date" type="datetime-local" value={eventForm.event_date} onChange={v => setEventForm(f => ({...f, event_date:v}))} required />
            <div className={styles.field}>
              <label className={styles.label}>Category</label>
              <select className="input" value={eventForm.category} onChange={e => setEventForm(f => ({...f, category:e.target.value, event_type:e.target.value}))}>
                {['Music','Movies','Social','Festival','Theater','Other'].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Age Rating</label>
              <select className="input" value={eventForm.age_rating} onChange={e => setEventForm(f => ({...f, age_rating:e.target.value}))}>
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
              <input type="checkbox" checked={eventForm.has_seat_selection}
                onChange={e => setEventForm(f => ({...f, has_seat_selection:e.target.checked}))} />
              Enable seat selection (movies)
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
                <input className="input" placeholder="Tier name (e.g. VIP)" value={t.name} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, name:e.target.value} : x))} />
                <input className="input" type="number" placeholder="Price (₹)" min="0" value={t.price} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, price:e.target.value} : x))} />
                <input className="input" type="number" placeholder="Seats" min="1" value={t.total_seats} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, total_seats:e.target.value} : x))} />
                <input className={styles.colorPicker} type="color" value={t.color} onChange={e => setTiers(ts => ts.map((x,j) => j===i ? {...x, color:e.target.value} : x))} title="Tier colour" />
                <button type="button" className={styles.removeTier} onClick={() => setTiers(ts => ts.filter((_,j) => j!==i))}>✕</button>
              </div>
            ))}
          </div>

          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Creating…' : 'Create Event'}</button>
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
      {tab === 4 && (
        <div className={styles.statsGrid}>
          <div className={styles.statCard}><span className={styles.statNum}>{myEvents.length}</span><span>Events Created</span></div>
          <div className={styles.statCard}><span className={styles.statNum}>{myVenues.length}</span><span>Venues Onboarded</span></div>
          <div className={styles.statCard}>
            <span className={styles.statNum}>{myEvents.reduce((s, e) => s + (e.total_tickets - e.available_tickets), 0).toLocaleString()}</span>
            <span>Tickets Sold</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statNum}>
              ₹{myEvents.reduce((s, e) => s + (e.total_tickets - e.available_tickets) * e.price, 0).toLocaleString('en-IN')}
            </span>
            <span>Estimated Revenue</span>
          </div>
        </div>
      )}
    </div>
  )
}
