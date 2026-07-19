import { useState, useEffect } from 'react'
import { createBooking, getTiers, getSeatAvailability } from '../lib/api'
import { useApp } from '../context/AppContext'
import styles from './BookingModal.module.css'

const ROWS = ['A','B','C','D','E','F']
const COLS = Array.from({ length: 10 }, (_, i) => i + 1)

function SeatMap({ bookedSeats, selected, onToggle, tiers }) {
  const tierColors = {}
  tiers.forEach((t, i) => {
    const rowsPerTier = Math.ceil(ROWS.length / tiers.length)
    for (let r = i * rowsPerTier; r < Math.min((i + 1) * rowsPerTier, ROWS.length); r++) {
      tierColors[ROWS[r]] = t.color
    }
  })
  return (
    <div className={styles.seatMap}>
      <div className={styles.screen}>SCREEN</div>
      {ROWS.map(row => (
        <div key={row} className={styles.seatRow}>
          <span className={styles.rowLabel}>{row}</span>
          {COLS.map(col => {
            const label = `${row}${col}`
            const isBooked   = bookedSeats.includes(label)
            const isSelected = selected.includes(label)
            return (
              <button
                key={col}
                className={`${styles.seat} ${isBooked ? styles.seatBooked : ''} ${isSelected ? styles.seatSelected : ''}`}
                style={!isBooked && !isSelected ? { borderColor: tierColors[row] || '#A78BFA', color: tierColors[row] || '#A78BFA' } : {}}
                onClick={() => !isBooked && onToggle(label)}
                disabled={isBooked}
                title={label}
              >{col}</button>
            )
          })}
        </div>
      ))}
      <div className={styles.seatLegend}>
        <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendAvail}`}/>Available</span>
        <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendSel}`}/>Selected</span>
        <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendBooked}`}/>Taken</span>
      </div>
    </div>
  )
}

export default function BookingModal() {
  const { bookingEvent, setBookingEvent, addToast, setEvents, events } = useApp()
  const ev = bookingEvent
  const [tiers, setTiers]             = useState([])
  const [bookedSeats, setBookedSeats] = useState([])
  const [selectedTier, setSelectedTier] = useState(null)
  const [qty, setQty]                 = useState(1)
  const [attendees, setAttendees]     = useState([{ full_name: '', age: '', phone: '', seat_label: '' }])
  const [selectedSeats, setSelectedSeats] = useState([])
  const [busy, setBusy]               = useState(false)
  const [err, setErr]                 = useState('')
  const [ageWarn, setAgeWarn]         = useState(false)

  const is18Plus = ev && (ev.age_rating === 'A' || ev.age_rating === '18+')
  const hasTiers = tiers.length > 0
  const hasSeatSel = ev?.has_seat_selection
  const activeTier = tiers.find(t => t.id === selectedTier) || null
  const unitPrice = activeTier ? activeTier.price : (ev?.price || 0)
  const maxQty = activeTier
    ? Math.min(activeTier.available_seats, hasSeatSel ? ROWS.length * COLS.length : 10)
    : Math.min(ev?.available_tickets || 0, 10)

  useEffect(() => {
    if (!ev) return
    getTiers(ev.id).then(r => {
      setTiers(r.data)
      if (r.data.length > 0) setSelectedTier(r.data[0].id)
    }).catch(() => {})
    if (ev.has_seat_selection) {
      getSeatAvailability(ev.id).then(r => setBookedSeats(r.data.booked_seats || [])).catch(() => {})
    }
  }, [ev?.id])

  useEffect(() => {
    setAttendees(Array.from({ length: qty }, (_, i) => attendees[i] || { full_name: '', age: '', phone: '', seat_label: '' }))
  }, [qty])

  if (!ev) return null

  function updateAttendee(i, field, val) {
    setAttendees(a => a.map((x, idx) => idx === i ? { ...x, [field]: val } : x))
  }

  function toggleSeat(label) {
    setSelectedSeats(s => {
      if (s.includes(label)) return s.filter(x => x !== label)
      if (s.length >= qty) return [...s.slice(1), label]
      return [...s, label]
    })
  }

  async function handleBook() {
    setErr('')
    if (is18Plus) {
      const minorNames = attendees.filter(a => a.age && parseInt(a.age) < 18).map(a => a.full_name)
      if (minorNames.length > 0) {
        setAgeWarn(true)
        setErr(`${minorNames.join(', ')} ${minorNames.length > 1 ? 'are' : 'is'} under 18. This event is ${ev.age_rating}+.`)
        return
      }
    }
    setBusy(true)
    try {
      const payload = {
        event_id: ev.id,
        tier_id: selectedTier || undefined,
        quantity: qty,
        attendees: attendees.map((a, i) => ({
          full_name: a.full_name || `Guest ${i + 1}`,
          age: a.age ? parseInt(a.age) : undefined,
          phone: a.phone || undefined,
          seat_label: hasSeatSel ? selectedSeats[i] : (a.seat_label || undefined),
        })),
      }
      await createBooking(payload)
      setEvents(events.map(e =>
        e.id === ev.id ? { ...e, available_tickets: Math.max(0, e.available_tickets - qty) } : e
      ))
      addToast(`Booked ${qty} ticket${qty > 1 ? 's' : ''} for "${ev.name}" 🎉`)
      setBookingEvent(null)
    } catch (ex) {
      const msg = ex.response?.data?.detail || 'Booking failed'
      setErr(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally { setBusy(false) }
  }

  const img = ev.image_url || 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=600&h=220&q=80'

  return (
    <div className="overlay" onClick={() => setBookingEvent(null)}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <button className={styles.close} onClick={() => setBookingEvent(null)}>✕</button>

        {/* Banner */}
        <div className={styles.banner}>
          <img src={img} alt={ev.name} />
          <div className={styles.bannerOverlay}>
            {is18Plus && <span className={styles.ageWarnBanner}>18+ Event — Age verification required</span>}
            <span className={styles.bannerCat}>{ev.category} · {ev.age_rating}</span>
            <h2 className={styles.bannerTitle}>{ev.name}</h2>
          </div>
        </div>

        <div className={styles.body}>
          <div className={styles.meta}>
            <span>📍 {ev.venue}</span>
            <span>📅 {new Date(ev.event_date).toLocaleDateString('en-IN', { day:'numeric', month:'long', year:'numeric' })}</span>
          </div>

          {/* 18+ warning */}
          {is18Plus && (
            <div className={styles.ageNotice}>
              ⚠️ This is an age-restricted event. All attendees must be 18 or older. You will be asked to provide age for each attendee.
            </div>
          )}

          {/* Tier selection */}
          {hasTiers && (
            <div className={styles.tierSection}>
              <p className={styles.sectionLabel}>Select ticket tier</p>
              <div className={styles.tierGrid}>
                {tiers.map(t => (
                  <button
                    key={t.id}
                    className={`${styles.tierCard} ${selectedTier === t.id ? styles.tierActive : ''}`}
                    style={{ '--tc': t.color }}
                    onClick={() => setSelectedTier(t.id)}
                    disabled={t.available_seats === 0}
                  >
                    <span className={styles.tierName}>{t.name}</span>
                    <span className={styles.tierPrice}>₹{t.price.toLocaleString('en-IN')}</span>
                    <span className={styles.tierAvail}>{t.available_seats === 0 ? 'Sold out' : `${t.available_seats} left`}</span>
                    {t.benefits && (
                      <ul className={styles.tierBenefits}>
                        {t.benefits.split(',').map(b => <li key={b}>✓ {b.trim()}</li>)}
                      </ul>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Quantity */}
          <div className={styles.qtyRow}>
            <label className={styles.qtyLabel}>Tickets</label>
            <div className={styles.qtyCtrl}>
              <button className={styles.qtyBtn} onClick={() => setQty(q => Math.max(1, q - 1))} disabled={qty <= 1}>−</button>
              <span className={styles.qtyNum}>{qty}</span>
              <button className={styles.qtyBtn} onClick={() => setQty(q => Math.min(maxQty, q + 1))} disabled={qty >= maxQty}>+</button>
            </div>
          </div>

          {/* Seat map */}
          {hasSeatSel && (
            <div className={styles.seatSection}>
              <p className={styles.sectionLabel}>Select {qty} seat{qty > 1 ? 's' : ''} ({selectedSeats.length}/{qty} chosen)</p>
              <SeatMap bookedSeats={bookedSeats} selected={selectedSeats} onToggle={toggleSeat} tiers={tiers} />
            </div>
          )}

          {/* Attendee forms */}
          <div className={styles.attendeeSection}>
            <p className={styles.sectionLabel}>Attendee details</p>
            {attendees.map((a, i) => (
              <div key={i} className={styles.attendeeCard}>
                <span className={styles.attendeeNum}>Ticket {i + 1}</span>
                <div className={styles.attendeeFields}>
                  <input className="input" placeholder="Full name *" value={a.full_name}
                    onChange={e => updateAttendee(i, 'full_name', e.target.value)} required />
                  <div className={styles.row2}>
                    <input className="input" placeholder={is18Plus ? 'Age (required)' : 'Age'} type="number"
                      min="0" max="120" value={a.age} onChange={e => updateAttendee(i, 'age', e.target.value)}
                      style={is18Plus && a.age && parseInt(a.age) < 18 ? { borderColor: '#EF4444' } : {}} />
                    <input className="input" placeholder="Phone" value={a.phone}
                      onChange={e => updateAttendee(i, 'phone', e.target.value)} />
                  </div>
                  {!hasSeatSel && (
                    <input className="input" placeholder="Seat preference (optional)" value={a.seat_label}
                      onChange={e => updateAttendee(i, 'seat_label', e.target.value)} />
                  )}
                  {hasSeatSel && selectedSeats[i] && (
                    <p className={styles.seatAssigned}>Seat: <strong>{selectedSeats[i]}</strong></p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Price summary */}
          <div className={styles.priceBox}>
            <div className={styles.priceLine}>
              <span>{unitPrice ? `₹${unitPrice.toLocaleString('en-IN')}` : 'Free'} × {qty}</span>
              <span className={styles.total}>{unitPrice ? `₹${(unitPrice * qty).toLocaleString('en-IN')}` : 'Free'}</span>
            </div>
          </div>

          {err && <p className={`${styles.err} ${ageWarn ? styles.errAge : ''}`}>{err}</p>}

          <button className={`btn btn-primary ${styles.confirmBtn}`} onClick={handleBook}
            disabled={busy || maxQty === 0 || (hasSeatSel && selectedSeats.length < qty)}>
            {busy ? 'Booking…' : `Confirm ${qty} ticket${qty > 1 ? 's' : ''} →`}
          </button>

          <p className={styles.note}>Booking confirmation will be logged to the server console.</p>
        </div>
      </div>
    </div>
  )
}
