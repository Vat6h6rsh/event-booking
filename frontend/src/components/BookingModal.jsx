import { useState } from 'react'
import { createBook } from '../lib/api'
import { useApp } from '../context/AppContext'
import styles from './BookingModal.module.css'

const FALLBACK = 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=600&h=280&q=80'

function fmtPrice(p) {
  if (!p) return 'Free'
  return `₹${(p).toLocaleString('en-IN')}`
}

export default function BookingModal() {
  const { bookingEvent, setBookingEvent, addToast, setEvents, events } = useApp()
  const ev = bookingEvent
  const [qty, setQty]   = useState(1)
  const [busy, setBusy] = useState(false)
  const [err, setErr]   = useState('')

  if (!ev) return null

  const maxQty  = Math.min(ev.available_tickets, 10)
  const total   = ev.price ? ev.price * qty : 0
  const img     = ev.image_url || FALLBACK

  async function handleBook() {
    setErr('')
    setBusy(true)
    try {
      await createBook(ev.id, qty)
      // Optimistically update available_tickets in state
      setEvents(events.map((e) =>
        e.id === ev.id ? { ...e, available_tickets: e.available_tickets - qty } : e
      ))
      addToast(`Booked ${qty} ticket${qty > 1 ? 's' : ''} for "${ev.name}" 🎉`)
      setBookingEvent(null)
    } catch (ex) {
      const msg = ex.response?.data?.detail || 'Booking failed'
      setErr(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="overlay" onClick={() => setBookingEvent(null)}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button className={styles.close} onClick={() => setBookingEvent(null)}>✕</button>

        {/* Event banner */}
        <div className={styles.banner}>
          <img src={img} alt={ev.name} />
          <div className={styles.bannerOverlay}>
            <span className={styles.bannerCat}>{ev.category}</span>
            <h2 className={styles.bannerTitle}>{ev.name}</h2>
          </div>
        </div>

        <div className={styles.body}>
          {/* Meta row */}
          <div className={styles.meta}>
            <span>📍 {ev.venue}</span>
            <span>📅 {new Date(ev.event_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
            <span>🎟️ {ev.available_tickets} tickets left</span>
          </div>

          {/* Qty */}
          <div className={styles.qtyRow}>
            <label className={styles.qtyLabel}>Tickets</label>
            <div className={styles.qtyCtrl}>
              <button className={styles.qtyBtn} onClick={() => setQty((q) => Math.max(1, q - 1))} disabled={qty <= 1}>−</button>
              <span className={styles.qtyNum}>{qty}</span>
              <button className={styles.qtyBtn} onClick={() => setQty((q) => Math.min(maxQty, q + 1))} disabled={qty >= maxQty}>+</button>
            </div>
          </div>

          {/* Price breakdown */}
          <div className={styles.priceBox}>
            <div className={styles.priceLine}>
              <span>{fmtPrice(ev.price)} × {qty}</span>
              <span className={styles.total}>{ev.price ? `₹${(total).toLocaleString('en-IN')}` : 'Free'}</span>
            </div>
          </div>

          {err && <p className={styles.err}>{err}</p>}

          <button
            className={`btn btn-primary ${styles.confirmBtn}`}
            onClick={handleBook}
            disabled={busy || maxQty === 0}
          >
            {busy ? 'Booking…' : `Confirm Booking 🎉`}
          </button>

          <p className={styles.note}>
            A confirmation will be sent to your email after booking.
          </p>
        </div>
      </div>
    </div>
  )
}
