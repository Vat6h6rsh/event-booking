import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext'
import { getVenues } from '../lib/api'
import { istDay, eventDate, eventCity } from '../lib/booking'
import EventCard from './EventCard'
import styles from './EventsSection.module.css'
export default function EventsSection() {
  const { events, eventsLoading, category, setCategory, filters, setFilters, eventsError, setCatalogueVersion } = useApp()
  const [cityDraft, setCityDraft] = useState(filters.city)
  useEffect(() => { setCityDraft(filters.city) }, [filters.city])
  const [venues, setVenues] = useState([])
  const [venueError, setVenueError] = useState(false)
  const [venueVersion, setVenueVersion] = useState(0)
  useEffect(() => {
    let ignore = false
    async function loadCities() {
      const all = []
      for (let skip = 0; ; skip += 100) {
        const { data } = await getVenues({ skip, limit: 100 })
        if (ignore) return
        all.push(...data)
        if (data.length < 100) break
      }
      if (!ignore) { setVenues(all); setVenueError(false) }
    }
    loadCities().catch(() => { if (!ignore) setVenueError(true) })
    return () => { ignore = true }
  }, [venueVersion])
  const cityFor = event => eventCity(event, venues)
  const cities = [...new Set(events.map(cityFor).filter(Boolean))].sort()
  const today = istDay(new Date().toISOString())
  const todayDate = new Date(`${today}T00:00:00+05:30`)
  const day = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Kolkata', weekday: 'short' }).format(todayDate)
  const daysUntilSaturday = day === 'Sun' ? 0 : (6 - ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(day) + 7) % 7
  const saturday = new Date(todayDate.getTime() + daysUntilSaturday * 86400000)
  const start = istDay(saturday.toISOString())
  const end = istDay(new Date(saturday.getTime() + (day === 'Sun' ? 0 : 86400000)).toISOString())
  const filtered = events.filter(e => {
    const date = istDay(e.event_date)
    const q = filters.q.trim().toLowerCase()
    return eventDate(e.event_date) > new Date() && (!filters.city || cityFor(e).toLowerCase() === filters.city.toLowerCase()) && (category === 'all' || e.category === category) && (!q || `${e.name} ${e.venue}`.toLowerCase().includes(q)) && (filters.date === 'all' || (filters.date === 'today' ? date === today : date >= start && date <= end))
  })
  const change = (key, value) => setFilters(f => ({ ...f, [key]: value }))
  const clear = () => { setFilters({ q: '', city: '', date: 'all' }); setCategory('all') }
  return <section id="events" className={`section ${styles.section}`}><div className="container">
    <div className="section-header"><span className="section-eyebrow">Live &amp; Upcoming</span><h2 className="section-title">Find your <span>next event</span></h2><p className="section-subtitle">Pick a city, a date, and something you love.</p></div>
    <div className={styles.filters} aria-label="Filter events">
      <label>Search events or venues<input className="input" type="search" value={filters.q} onChange={e => change('q', e.target.value)} placeholder="Event or venue name" /></label>
      <div><label>City<input className="input" list="event-cities" value={cityDraft} onChange={e => setCityDraft(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') change('city', cityDraft.trim()) }} placeholder="All cities, or type Patna / Ranchi" /></label><datalist id="event-cities">{cities.map(c => <option key={c} value={c} />)}</datalist><button className="btn btn-secondary btn-sm" onClick={() => change('city', cityDraft.trim())}>Apply city</button></div>
      <div className={styles.chips} role="group" aria-label="Date in IST">{[['all', 'All upcoming'], ['today', 'Today'], ['weekend', 'This weekend']].map(([id, label]) => <button key={id} className={`btn ${filters.date === id ? 'btn-primary' : 'btn-secondary'}`} aria-pressed={filters.date === id} onClick={() => change('date', id)}>{label}</button>)}</div>
    </div>
    <div className={styles.applied}><p role="status">{eventsLoading ? 'Loading events...' : `${filtered.length} events`} · {filters.city || 'All cities'} · {category === 'all' ? 'All categories' : category}{filters.q && ` · Search: ${filters.q}`}{filters.date === 'today' ? ` · ${today} IST` : filters.date === 'weekend' ? ` · ${start} – ${end} IST` : ''}</p><button className="btn btn-ghost" onClick={clear}>Clear all filters</button></div>
    {venueError && <p role="alert">City details could not be refreshed. <button className="btn btn-secondary btn-sm" onClick={() => setVenueVersion(v => v + 1)}>Retry cities</button></p>}
    {eventsError && <div role="alert" className={styles.empty}><p>{eventsError} {events.length > 0 && 'Previously loaded events may be out of date.'}</p><button className="btn btn-secondary" onClick={() => setCatalogueVersion(v => v + 1)}>Retry events</button></div>}
    {eventsLoading ? <><p role="status">Loading upcoming events...</p><div className={styles.grid} aria-hidden="true">{[1,2,3].map(n => <div key={n} className={styles.skeletonCard}><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /></div>)}</div></> : filtered.length ? <div className={styles.grid}>{filtered.map(ev => <EventCard key={ev.id} event={{ ...ev, _city: cityFor(ev) }} />)}</div> : !eventsError && <div className={styles.empty}><p>No upcoming events match these filters.</p><button className="btn btn-secondary" onClick={clear}>Show all upcoming events</button></div>}
  </div></section>
}
