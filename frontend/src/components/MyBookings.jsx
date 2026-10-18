import { useState, useEffect, useRef } from 'react'
import { myBookings, cancelBooking, getEvent } from '../lib/api'
import { errorDetail, eventDate } from '../lib/booking'
import { useApp } from '../context/AppContext'
import BookingReceipt from './BookingReceipt'
import styles from './MyBookings.module.css'
export default function MyBookings() {
  const { user, goHome, setCatalogueVersion } = useApp()
  const [items, setItems] = useState([])
  const [events, setEvents] = useState({})
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')
  const [version, setVersion] = useState(0)
  const [confirm, setConfirm] = useState(null)
  const [busy, setBusy] = useState(null)
  const [message, setMessage] = useState('')
  const lock = useRef(false)
  useEffect(() => {
    if (user?.role !== 'customer') return
    let ignore = false
    setLoading(true); setErr('')
    myBookings().then(async r => {
      if (ignore) return
      setItems(r.data)
      const ids = [...new Set(r.data.map(b => b.event_id))]
      const results = await Promise.allSettled(ids.map(id => getEvent(id)))
      if (ignore) return
      setEvents(Object.fromEntries(results.flatMap((r, i) => r.status === 'fulfilled' ? [[ids[i], r.value.data]] : [])))
      if (results.some(r => r.status === 'rejected')) setErr('Some event details could not be loaded. Your bookings are shown below; retry to refresh dates and venues.')
    }).catch(ex => { if (!ignore) setErr(errorDetail(ex, 'Could not load your tickets. Please retry.')) }).finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [user?.id, version])
  async function cancel(id) {
    if (lock.current) return
    lock.current = true; setBusy(id); setErr('')
    try { await cancelBooking(id); setItems(a => a.map(b => b.id === id ? { ...b, status: 'cancelled' } : b)); setConfirm(null); setMessage(`Booking #${id} cancelled.`); setCatalogueVersion(v => v + 1) }
    catch (ex) { setErr(errorDetail(ex, 'Cancellation could not be confirmed. Refresh your tickets before retrying.')) }
    finally { lock.current = false; setBusy(null) }
  }
  if (user?.role !== 'customer') return <div className={styles.page}><h1>My tickets</h1><p>Log in as a customer to view your tickets.</p></div>
  return <div className={styles.page}><div className={styles.heading}><h1>My tickets</h1><button className="btn btn-secondary" disabled={loading || busy !== null} onClick={() => setVersion(v => v + 1)}>Refresh tickets</button></div>
    <p role="status">{message}</p>
    {err && <p role="alert" className={styles.error}>{err}</p>}
    {loading && <div role="status"><div className="skeleton" />Loading your tickets...</div>}
    {!loading && !items.length && !err && <><p>No bookings yet. Find your next event.</p><button className="btn btn-primary" onClick={goHome}>Explore events</button></>}
    <div className={styles.list}>{items.map(b => <article key={b.id}>
      <BookingReceipt booking={b} event={events[b.event_id]} fresh={false} />
      {b.status === 'confirmed' && <div className={styles.actions}>
        {confirm === b.id ? <><p>Cancel booking #{b.id}? Your tickets will no longer be valid. This does not issue a payment refund.</p><button className="btn btn-secondary" disabled={busy !== null} onClick={() => setConfirm(null)}>Keep tickets</button><button className="btn btn-primary" disabled={busy !== null} onClick={() => cancel(b.id)}>{busy === b.id ? 'Cancelling...' : 'Confirm cancellation'}</button></> : <button className="btn btn-secondary" disabled={busy !== null || !events[b.event_id] || eventDate(events[b.event_id].event_date) <= new Date()} onClick={() => setConfirm(b.id)}>Cancel booking</button>}
        {events[b.event_id] && eventDate(events[b.event_id].event_date) <= new Date() && <p>Cancellation is unavailable after the event starts.</p>}
      </div>}
    </article>)}</div>
  </div>
}
