import styles from './EventCard.module.css'
import { useApp } from '../context/AppContext'

const FALLBACK = {
  Music:   'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=600&h=380&q=80',
  Movies:  'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&h=380&q=80',
  Social:  'https://images.unsplash.com/photo-1527529482837-4698179dc6ce?auto=format&fit=crop&w=600&h=380&q=80',
  Festival:'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?auto=format&fit=crop&w=600&h=380&q=80',
  default: 'https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&h=380&q=80',
}
const CAT_BADGE = { Music:'badge-music', Movies:'badge-movies', Social:'badge-social', Festival:'badge-other' }
const AGE_COLOR = { 'U':'#22C55E','UA':'#F59E0B','A':'#EF4444','18+':'#DC2626' }

function timeColor(isoDate) {
  const h = new Date(isoDate).getHours()
  if (h < 12) return { bg: '#EFF6FF', color: '#1D4ED8', label: 'Morning' }
  if (h < 17) return { bg: '#FFFBEB', color: '#B45309', label: 'Afternoon' }
  if (h < 21) return { bg: '#F5F3FF', color: '#6D28D9', label: 'Evening' }
  return { bg: '#1E1B4B', color: '#C4B5FD', label: 'Night' }
}

function lowestTierPrice(tiers) {
  if (!tiers?.length) return null
  return Math.min(...tiers.map(t => t.price))
}

export default function EventCard({ event }) {
  const { openBooking, goToEvent } = useApp()
  const img      = event.image_url || FALLBACK[event.category] || FALLBACK.default
  const sold     = event.available_tickets === 0
  const lowStock = !sold && event.available_tickets <= 15
  const tc       = timeColor(event.event_date)
  const minPrice = lowestTierPrice(event.tiers)
  const displayPrice = minPrice ?? event.price

  function fmtPrice(p) {
    return p ? `from ₹${p.toLocaleString('en-IN')}` : 'Free'
  }
  function fmtDate(iso) {
    return new Date(iso).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' })
  }

  return (
    <article className={`card ${styles.card}`} onClick={() => goToEvent(event)}>
      <div className={styles.imgWrap}>
        <img src={img} alt={event.name} loading="lazy" />

        {/* Category badge */}
        <span className={`badge ${CAT_BADGE[event.category] || 'badge-other'} ${styles.catBadge}`}>
          {event.category}
        </span>

        {/* Age rating */}
        <span className={styles.ageBadge} style={{ background: AGE_COLOR[event.age_rating] || '#6B7280' }}>
          {event.age_rating}
        </span>

        {/* Screening time */}
        <span className={styles.timeBadge} style={{ background: tc.bg, color: tc.color }}>
          {new Date(event.event_date).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit', hour12:true })}
        </span>

        {sold && <span className={styles.soldBadge}>Sold Out</span>}
        {lowStock && !sold && (
          <span className={styles.lowBadge}>Only {event.available_tickets} left!</span>
        )}
      </div>

      <div className={styles.body}>
        <h3 className={styles.name}>{event.name}</h3>

        <div className={styles.meta}>
          <span>📍 {event.venue}</span>
          <span>📅 {fmtDate(event.event_date)}</span>
        </div>

        {/* Tier pills */}
        {event.tiers?.length > 0 && (
          <div className={styles.tiers}>
            {event.tiers.slice(0, 3).map(t => (
              <span key={t.id} className={styles.tierPill} style={{ background: t.color + '22', color: t.color, borderColor: t.color + '55' }}>
                {t.name}
              </span>
            ))}
          </div>
        )}

        <div className={styles.footer}>
          <div className={styles.priceWrap}>
            <span className={styles.price}>{fmtPrice(displayPrice)}</span>
            <span className={styles.tickets}>{sold ? '— Sold out' : `🎟️ ${event.available_tickets} left`}</span>
          </div>
          <button
            className={`btn btn-primary btn-sm ${sold ? styles.soldBtn : ''}`}
            onClick={(e) => { e.stopPropagation(); openBooking(event) }}
            disabled={sold}
          >
            {sold ? 'Sold Out' : 'Book →'}
          </button>
        </div>
      </div>
    </article>
  )
}
