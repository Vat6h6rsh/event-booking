import { useState, useEffect } from 'react'
import { getEvent, getTiers } from '../lib/api'
import { useApp } from '../context/AppContext'
import styles from './EventDetail.module.css'

const AGE_COLOR = { U:'#22C55E', UA:'#F59E0B', A:'#EF4444', '18+':'#DC2626' }

export default function EventDetail() {
  const { selectedEvent, goHome, openBooking } = useApp()
  const [ev, setEv]     = useState(selectedEvent)
  const [tiers, setTiers] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!selectedEvent) return
    setLoading(true)
    Promise.all([
      getEvent(selectedEvent.id),
      getTiers(selectedEvent.id),
    ]).then(([evRes, tiersRes]) => {
      setEv(evRes.data)
      setTiers(tiersRes.data)
    }).finally(() => setLoading(false))
  }, [selectedEvent?.id])

  if (!ev) return null

  const banner = ev.banner_url || ev.image_url || 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=1200&h=450&q=80'
  const is18Plus = ev.age_rating === 'A' || ev.age_rating === '18+'
  const sold     = ev.available_tickets === 0

  return (
    <div className={styles.page}>
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
            <span>📅 {new Date(ev.event_date).toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long', year:'numeric' })}</span>
            {ev.end_date && <span>🏁 Ends {new Date(ev.end_date).toLocaleDateString('en-IN')}</span>}
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
          {loading && <p className={styles.loading}>Loading…</p>}
          {!loading && tiers.length === 0 && (
            <div className={styles.basePricing}>
              <span className={styles.basePrice}>{ev.price ? `₹${ev.price.toLocaleString('en-IN')}` : 'Free'}</span>
              <span className={styles.baseAvail}>{sold ? 'Sold out' : `${ev.available_tickets} tickets left`}</span>
              <button className="btn btn-primary" onClick={() => openBooking(ev)} disabled={sold}>
                {sold ? 'Sold Out' : 'Book Now →'}
              </button>
            </div>
          )}
          {!loading && tiers.length > 0 && (
            <div className={styles.tierGrid}>
              {tiers.map(t => {
                const tierSold = t.available_seats === 0
                const tierLow  = !tierSold && t.available_seats <= 10
                return (
                  <div key={t.id} className={styles.tierCard} style={{ '--tc': t.color }}>
                    <div className={styles.tierHead}>
                      <span className={styles.tierName}>{t.name}</span>
                      {tierSold && <span className={styles.tierSold}>Sold out</span>}
                      {tierLow  && <span className={styles.tierLow}>Only {t.available_seats} left!</span>}
                    </div>
                    <span className={styles.tierPrice}>
                      {t.price ? `₹${t.price.toLocaleString('en-IN')}` : 'Free'}
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
                      disabled={tierSold}
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
            🪑 This event features <strong>seat selection</strong>. Choose your seats during booking.
          </div>
        )}
      </div>
    </div>
  )
}
