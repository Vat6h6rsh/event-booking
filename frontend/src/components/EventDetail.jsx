import { useState, useEffect } from 'react'
import { formatMoney } from '../lib/money'
import { formatDate, errorDetail, inventory, eventDate } from '../lib/booking'
import { getEvent, getTiers } from '../lib/api'
import { useApp } from '../context/AppContext'
import styles from './EventDetail.module.css'

const AGE_COLOR = { U:'#22C55E', UA:'#F59E0B', A:'#EF4444', '18+':'#DC2626' }

// Themed pages — each category paints the detail page with its own accent color.
const CATEGORY_THEME = {
  Music:    '#E0122B',
  Movies:   '#7C3AED',
  Social:   '#C2410C',
  Festival: '#C4321A',
  Sports:   '#15803D',
  Food:     '#A85B04',
  Tech:     '#0369A1',
  Art:      '#8530CB',
  Wellness: '#047857',
  Comedy:   '#CB163D',
  default:  '#E0122B',
}

export default function EventDetail() {
  const { selectedEvent, goHome, openBooking, bookingEvent } = useApp()
  const [ev, setEv]     = useState(selectedEvent)
  const [tiers, setTiers] = useState([])
  const [loading, setLoading] = useState(true)

  const [error, setError] = useState('')
  const [version, setVersion] = useState(0)
  useEffect(() => {
    if (!selectedEvent) return
    let ignore = false
    setLoading(true); setError('')
    Promise.all([getEvent(selectedEvent.id), getTiers(selectedEvent.id)]).then(([evRes, tiersRes]) => {
      if (!ignore) { setEv(evRes.data); setTiers(tiersRes.data) }
    }).catch(ex => { if (!ignore) setError(errorDetail(ex, 'Could not load event and ticket options. Please retry.')) })
      .finally(() => { if (!ignore) setLoading(false) })
    return () => { ignore = true }
  }, [selectedEvent, version])

  if (!ev) return null

  const banner = ev.banner_url || ev.image_url || '/images/events/music-01.jpg'
  const is18Plus = ev.age_rating === 'A' || ev.age_rating === '18+'
  const stock = inventory(ev, tiers)
  const sold = stock.sold || eventDate(ev.event_date) <= new Date()
  const blocked = sold || loading || !!error
  const accent   = CATEGORY_THEME[ev.category] || CATEGORY_THEME.default

  return (
    <div className={styles.page} style={{ '--primary': accent }}>
      {/* Back */}
      <button className={styles.back} onClick={goHome}>← Back to events</button>

      {/* 18+ Warning */}
      {is18Plus && (
        <div className={styles.ageWall}>
          <span className={styles.ageIcon}>🔞</span>
          <h3>Age-Restricted Event</h3>
          <p>This event is rated <strong>{ev.age_rating}</strong>. You must be 18 or older to attend. Age verification will be required at booking.</p>
        </div>
      )}

      {/* Banner */}
      <div className={styles.banner}>
        <img src={banner} alt={ev.name} />
        <div className={styles.bannerOverlay}>
          <span className={styles.cat}>{ev.category}</span>
          <h1 className={styles.title}>{ev.name}</h1>
          <div className={styles.metaBanner}>
            <span>📍 {ev.venue}</span>
            <span>📅 {formatDate(ev.event_date)}</span>
            {ev.end_date && <span>🏁 Ends {formatDate(ev.end_date)}</span>}
          </div>
        </div>
      </div>

      <div className={styles.content}>
        {/* Tags & rating */}
        <div className={styles.tags}>
          <span className={styles.ageTag} style={{ background: AGE_COLOR[ev.age_rating] }}>
            Rated {ev.age_rating}
          </span>
          {ev.tags && ev.tags.split(',').map(t => (
            <span key={t} className={styles.tag}>{t.trim()}</span>
          ))}
        </div>

        {/* Description */}
        {ev.description && (
          <div className={styles.desc}>
            <h2 className={styles.secHead}>About this event</h2>
            <p>{ev.description}</p>
          </div>
        )}

        {/* Tiers / pricing */}
        <div>
          <h2 className={styles.secHead}>Ticket options</h2>
          {loading && <div role="status"><div className="skeleton" />Loading current ticket options…</div>}{error && <div role="alert"><p>{error}</p><button className="btn btn-secondary" onClick={() => setVersion(v => v + 1)}>Retry event and tickets</button></div>}
          {!loading && !error && tiers.length === 0 && (
            <div className={styles.basePricing}>
              <span className={styles.basePrice}>{formatMoney(ev.price)}</span>
              <span className={styles.baseAvail}>{sold ? 'Sold out' : `${ev.available_tickets} tickets left`}</span>
              <button className="btn btn-primary" onClick={() => openBooking(ev)} disabled={blocked}>
                {sold ? 'Sold Out' : 'Book Now →'}
              </button>
            </div>
          )}
          {!loading && !error && tiers.length > 0 && (
            <div className={styles.tierGrid}>
              {tiers.map(t => {
                const tierSold = t.available_seats === 0
                const tierLow  = !tierSold && t.available_seats <= 10
                return (
                  <div key={t.id} className={styles.tierCard} style={{ '--tc': t.color }}>
                    <div className={styles.tierHead}>
                      <span className={styles.tierName}>{t.name}</span>
                      {tierSold && <span className={styles.tierSold}>Sold out</span>}
                      {tierLow  && <span className={styles.tierLow}>{t.available_seats} available</span>}
                    </div>
                    <span className={styles.tierPrice}>
                      {formatMoney(t.price)}
                    </span>
                    {t.description && <p className={styles.tierDesc}>{t.description}</p>}
                    {t.benefits && (
                      <ul className={styles.tierPerks}>
                        {t.benefits.split(',').map(b => <li key={b}>✓ {b.trim()}</li>)}
                      </ul>
                    )}
                    <button
                      className={`btn btn-primary btn-sm ${styles.tierBtn}`}
                      onClick={() => openBooking({ ...ev, _preferTier: t.id })}
                      disabled={tierSold || blocked}
                    >
                      {tierSold ? 'Sold Out' : 'Book this tier →'}
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Seat selection notice */}
        {ev.has_seat_selection && (
          <div className={styles.seatNotice}>
            Reserved-seat selection is unavailable. Book general admission or a ticket tier; no specific seat is assigned.
          </div>
        )}
        <p className={styles.seatNotice}>Admission rating: {ev.age_rating}. {is18Plus ? 'All attendees must be 18 or older.' : 'Check organizer guidance for any additional admission rules.'} No payment is collected in this demo. Cancellation is available before the event starts through My tickets. For event-specific policies, contact support.</p>
      </div>
      {!bookingEvent && <div className={styles.mobileCta}><strong>{loading ? 'Loading tickets...' : error ? 'Tickets unavailable' : sold ? 'Unavailable' : `From ${formatMoney(stock.price)}`}</strong><button className="btn btn-primary" onClick={() => openBooking(ev)} disabled={blocked}>Select tickets</button></div>}
    </div>
  )
}
