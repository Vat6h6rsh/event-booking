import { useState, useEffect, useRef } from 'react'
import { createBooking, getTiers, getEvent } from '../lib/api'
import { useApp } from '../context/AppContext'
import { fireConfetti } from '../lib/confetti'
import { formatMoney } from '../lib/money'
import { errorDetail, formatDate, eventDate, retryDelay } from '../lib/booking'
import { useDialog } from '../lib/useDialog'
import BookingReceipt from './BookingReceipt'
import styles from './BookingModal.module.css'

// Prototype retained for future server-backed geometry and exclusive seat assignment.
// Public checkout must never send these client-generated seat labels.
const RESERVED_SEATS_ENABLED = false
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

const emptyAttendee = () => ({ full_name: '', age: '', phone: '' })
export default function BookingModal() {
  const { bookingEvent, setBookingEvent, setEvents, setSelectedEvent, setPage, PAGES, bookingIntents } = useApp()
  const savedDraft = bookingIntents.current.get(bookingEvent.id)?.draft
  const [ev, setEv] = useState(bookingEvent)
  const [tiers, setTiers] = useState([])
  const [tier, setTier] = useState(null)
  const [qty, setQty] = useState(savedDraft?.qty || 1)
  const [attendees, setAttendees] = useState(savedDraft?.attendees || [emptyAttendee()])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [version, setVersion] = useState(0)
  const [err, setErr] = useState('')
  const [fields, setFields] = useState({})
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [receipt, setReceipt] = useState(null)
  const [uncertain, setUncertain] = useState(false)
  const lock = useRef(false)
  const alive = useRef(true)
  const firstLoad = useRef(true)
  const timer = useRef(null)
  const stopWait = useRef(null)
  const close = () => { if (!lock.current) setBookingEvent(null) }
  const dialog = useDialog(close, busy)
  const active = tiers.find(t => t.id === tier)
  const restricted = ['A', '18+'].includes(ev.age_rating)
  const max = Math.min(10, ev.available_tickets, tiers.length ? active?.available_seats || 0 : ev.available_tickets)
  const unit = active?.price ?? ev.price
  const canChoose = !loading && !loadError && max > 0
  const expired = eventDate(ev.event_date) <= new Date()

  useEffect(() => { alive.current = true; return () => { alive.current = false; clearTimeout(timer.current); stopWait.current?.() } }, [])
  useEffect(() => {
    let ignore = false
    setLoading(true); setLoadError('')
    Promise.all([getEvent(bookingEvent.id), getTiers(bookingEvent.id)]).then(([e, t]) => {
      if (ignore) return
      setEv(e.data); setTiers(t.data)
      if (firstLoad.current) {
        const preferred = t.data.find(x => x.id === (savedDraft?.tier ?? bookingEvent._preferTier) && x.available_seats > 0)
        setTier(preferred?.id ?? t.data.find(x => x.available_seats > 0)?.id ?? null)
        firstLoad.current = false
      } else {
        setTier(previous => {
          if (t.data.length && !t.data.some(x => x.id === previous && x.available_seats > 0)) {
            setStatus('Your tier is no longer available. Please choose another tier.'); return null
          }
          return previous
        })
      }
      setEvents(list => list.map(x => x.id === e.data.id ? { ...e.data, tiers: t.data } : x))
      setSelectedEvent(previous => previous?.id === e.data.id ? { ...e.data, tiers: t.data } : previous)
    }).catch(ex => { if (!ignore) setLoadError(errorDetail(ex, 'Could not load current ticket options. Retry to continue.')) })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [bookingEvent.id, version])

  useEffect(() => {
    if (loading || loadError) return
    if (qty > Math.max(1, max)) { setQty(Math.max(1, max)); setStatus('Quantity adjusted to current availability (up to 10 per order).') }
  }, [max, loading, loadError, qty])
  useEffect(() => { setAttendees(a => Array.from({ length: qty }, (_, i) => a[i] || emptyAttendee())) }, [qty])

  const ticketsPage = () => { if (!lock.current) { setBookingEvent(null); setPage(PAGES.BOOKINGS) } }
  function update(i, field, value) { setAttendees(a => a.map((x, j) => j === i ? { ...x, [field]: value } : x)) }
  async function submit(e) {
    e.preventDefault()
    if (lock.current || receipt || loading || loadError || expired || !max || qty > max || attendees.length !== qty || (tiers.length && !active)) return
    const errors = {}
    attendees.forEach((a, i) => {
      if (!a.full_name.trim()) errors[`name-${i}`] = 'Enter a full name.'
      if ((restricted && !a.age.trim()) || (a.age !== '' && (!Number.isInteger(Number(a.age)) || Number(a.age) < (restricted ? 18 : 0) || Number(a.age) > 120))) errors[`age-${i}`] = restricted ? 'Enter an age from 18 to 120.' : 'Enter an age from 0 to 120.'
    })
    setFields(errors); setErr('')
    if (Object.keys(errors).length) { requestAnimationFrame(() => document.getElementById(Object.keys(errors)[0])?.focus()); return }
    const payload = { event_id: ev.id, tier_id: active?.id, quantity: qty, attendees: attendees.map(a => ({ full_name: a.full_name.trim(), age: a.age === '' ? undefined : Number(a.age), phone: a.phone.trim() || undefined })) }
    const signature = JSON.stringify(payload)
    let intent = bookingIntents.current.get(ev.id)
    if (!intent || intent.signature !== signature) {
      intent = { signature, key: crypto.randomUUID() }; bookingIntents.current.set(ev.id, intent)
    }
    intent.draft = { qty, tier, attendees }
    lock.current = true; setBusy(true); setUncertain(false); setStatus('Booking your tickets...')
    const slow = setTimeout(() => { if (alive.current) setStatus('Still checking your booking. Please keep this dialog open.') }, 10000)
    try {
      for (let retry = 0; ; retry++) {
        try {
          const { data } = await createBooking(payload, intent.key)
          bookingIntents.current.delete(ev.id) // intent fulfilled: a later purchase must get a fresh key
          if (!alive.current) return
          setReceipt(data); setStatus('Booking confirmed. Your ticket details are ready.'); fireConfetti()
          setVersion(v => v + 1)
          break
        } catch (ex) {
          if (ex.response?.status === 503 && retry < 3) {
            clearTimeout(slow)
            setStatus(`High demand, retrying... (${retry + 1} of 3). Please keep this dialog open.`)
            await new Promise(resolve => { stopWait.current = resolve; timer.current = setTimeout(resolve, retryDelay(ex.response.headers?.['retry-after'])) })
            if (!alive.current) return
            continue
          }
          if (ex.response?.status === 409) setVersion(v => v + 1)
          const unknown = !ex.response || ex.response.status >= 500
          setUncertain(unknown)
          setErr(errorDetail(ex, unknown ? 'We could not confirm the outcome. Check My tickets, or retry this same request safely.' : 'Booking failed. Please check your details.'))
          setStatus(ex.response?.status === 503 ? 'Demand is still high. You can retry when ready.' : '')
          break
        }
      }
    } finally { clearTimeout(slow); lock.current = false; if (alive.current) setBusy(false) }
  }
  return (
    <dialog ref={dialog} className={styles.modal} aria-labelledby="booking-title" onClick={e => { if (e.target === e.currentTarget) close() }}>
      <button className={styles.close} aria-label="Close booking" onClick={close} disabled={busy}>×</button>
      <div className={styles.banner}>
        <img src={ev.image_url || '/images/events/music-01.jpg'} alt="" />
        <div className={styles.bannerOverlay}><span className={styles.bannerCat}>{ev.category} · Admission: {ev.age_rating}</span><h2 id="booking-title" className={styles.bannerTitle}>{ev.name}</h2></div>
      </div>
      <div className={styles.body}>
        <p>{formatDate(ev.event_date)} · {ev.venue}</p>
        <p role="status">{status}</p>
        {receipt ? <>{loadError && <p role="status">Your booking is confirmed. Availability could not be refreshed; reopen the event for current ticket options.</p>}<BookingReceipt booking={receipt} event={ev} /><button className="btn btn-primary" onClick={ticketsPage}>View My tickets</button></> : <>
          {loading && <div role="status"><div className="skeleton" />Loading current ticket options...</div>}
          {loadError && <div role="alert"><p>{loadError}</p><button className="btn btn-secondary" onClick={() => setVersion(v => v + 1)}>Retry ticket options</button></div>}
          <form onSubmit={submit} noValidate>
            <fieldset disabled={busy || loading || !!loadError || expired} className={styles.fields}>
              {restricted && <p className={styles.ageNotice}>All attendees must be 18 or older. Age is required for each attendee.</p>}
              {tiers.length > 0 && <fieldset><legend>Select ticket tier</legend><div className={styles.tierGrid}>{tiers.map(t => <label key={t.id} className={`${styles.tierCard} ${tier === t.id ? styles.tierActive : ''}`} style={{ '--tc': t.color }}>
                <span><input type="radio" name="tier" checked={tier === t.id} onChange={() => setTier(t.id)} disabled={!t.available_seats} /> {t.name}</span>
                <strong>{formatMoney(t.price)} / ticket</strong><span>{t.available_seats ? `${t.available_seats} available` : 'Sold out'}</span>{t.benefits && <small>{t.benefits}</small>}
              </label>)}</div></fieldset>}
              {canChoose && <>
              <div className={styles.qtyRow}><span id="quantity-label">Tickets (maximum {max})</span><div className={styles.qtyCtrl} role="group" aria-labelledby="quantity-label">
                <button type="button" className={styles.qtyBtn} aria-label="Remove one ticket" disabled={qty <= 1} onClick={() => setQty(q => q - 1)}>−</button><output aria-label="Ticket quantity">{qty}</output><button type="button" className={styles.qtyBtn} aria-label="Add one ticket" disabled={qty >= max} onClick={() => setQty(q => q + 1)}>+</button>
              </div></div>
              <p className={styles.note}>General admission / tier booking only. Availability is checked when you confirm; tickets are not held.</p>
              {RESERVED_SEATS_ENABLED && <SeatMap bookedSeats={[]} selected={[]} onToggle={() => {}} tiers={tiers} />}
              {Object.keys(fields).length > 0 && <div role="alert" className={styles.err}><p>Please correct attendee details:</p>{Object.entries(fields).map(([id, message]) => <p key={id}><a href={`#${id}`} onClick={e => { e.preventDefault(); document.getElementById(id)?.focus() }}>{message} (ticket {Number(id.split('-')[1]) + 1})</a></p>)}</div>}
              {attendees.map((a, i) => <fieldset key={i} className={styles.attendeeCard}><legend>Ticket {i + 1}</legend>
                <label htmlFor={`name-${i}`}>Full name (required)</label><input className="input" id={`name-${i}`} autoComplete="name" value={a.full_name} onChange={e => update(i, 'full_name', e.target.value)} required aria-invalid={!!fields[`name-${i}`]} aria-describedby={fields[`name-${i}`] ? `name-error-${i}` : undefined} />
                {fields[`name-${i}`] && <p id={`name-error-${i}`} className={styles.err}>{fields[`name-${i}`]}</p>}
                <label htmlFor={`age-${i}`}>Age {restricted ? '(required, 18+)' : '(optional)'}</label><input className="input" id={`age-${i}`} type="number" min={restricted ? 18 : 0} max="120" step="1" required={restricted} value={a.age} onChange={e => update(i, 'age', e.target.value)} aria-invalid={!!fields[`age-${i}`]} aria-describedby={fields[`age-${i}`] ? `age-error-${i}` : undefined} />
                {fields[`age-${i}`] && <p id={`age-error-${i}`} className={styles.err}>{fields[`age-${i}`]}</p>}
                <label htmlFor={`phone-${i}`}>Phone (optional)</label><input className="input" id={`phone-${i}`} type="tel" autoComplete="tel" value={a.phone} onChange={e => update(i, 'phone', e.target.value)} />
              </fieldset>)}
              </>}
            </fieldset>
            {!loading && !loadError && !max && <p role="status">{tiers.some(t => t.available_seats > 0) && ev.available_tickets > 0 ? 'Choose another available tier to continue.' : 'Sold out. No tickets are currently available.'}</p>}
            {canChoose && <div className={styles.priceBox}><div className={styles.priceLine}><span>{formatMoney(unit)} × {qty}</span><strong>{formatMoney(unit * qty)}</strong></div><p>No payment is collected in this demo.</p></div>}
            {err && (uncertain || max > 0 || loading || loadError) && <p role="alert" className={styles.err}>{err}</p>}
            {uncertain && <button type="button" className="btn btn-secondary" onClick={ticketsPage} disabled={busy}>Check My tickets</button>}
            {(max > 0 || uncertain || loading || loadError) && <button className={`btn btn-primary ${styles.confirmBtn}`} type="submit" disabled={busy || loading || !!loadError || !max || qty > max || expired || (tiers.length > 0 && !active)}>{busy ? 'Booking...' : uncertain ? 'Retry same booking' : expired ? 'Event has started' : 'Confirm tickets'}</button>}
          </form>
        </>}
      </div>
    </dialog>
  )
}
