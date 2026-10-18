import { formatMoney } from '../lib/money'
import { inventory, formatDate, eventDate, eventCity } from '../lib/booking'
import styles from './EventCard.module.css'
import { useApp } from '../context/AppContext'

const FALLBACK = {
  Music:    '/images/events/music-01.jpg',
  Movies:   '/images/events/movies-01.jpg',
  Social:   '/images/events/food-01.jpg',
  Festival: '/images/events/festival-01.jpg',
  Sports:   '/images/events/sports-01.jpg',
  Food:     '/images/events/food-04.jpg',
  Tech:     '/images/events/tech-01.jpg',
  Art:      '/images/events/art-01.jpg',
  Wellness: '/images/events/wellness-01.jpg',
  Comedy:   '/images/events/comedy-01.jpg',
  default:  '/images/events/music-06.jpg',
}
const CAT_BADGE = {
  Music:'badge-music', Movies:'badge-movies', Social:'badge-social', Festival:'badge-festival',
  Sports:'badge-sports', Food:'badge-food', Tech:'badge-tech', Art:'badge-art',
  Wellness:'badge-wellness', Comedy:'badge-comedy',
}
const AGE_COLOR = { 'U':'#22C55E','UA':'#F59E0B','A':'#EF4444','18+':'#DC2626' }

function timeColor(isoDate) {
  const h = Number(eventDate(isoDate).toLocaleString('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit' }))
  if (h < 12) return { bg: '#EFF6FF', color: '#1D4ED8', label: 'Morning' }
  if (h < 17) return { bg: '#FFFBEB', color: '#B45309', label: 'Afternoon' }
  if (h < 21) return { bg: '#F5F3FF', color: '#6D28D9', label: 'Evening' }
  return { bg: '#1E1B4B', color: '#C4B5FD', label: 'Night' }
}

export default function EventCard({ event }) {
  const { openBooking, goToEvent } = useApp()
  const img      = event.image_url || FALLBACK[event.category] || FALLBACK.default
  const stock = inventory(event)
  const sold = stock.sold || eventDate(event.event_date) <= new Date()
  const lowStock = !sold && stock.available <= 15
  const tc       = timeColor(event.event_date)
  const displayPrice = stock.price

  function fmtPrice(p) {
    return sold ? 'Unavailable' : `From ${formatMoney(p)}`
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
          {eventDate(event.event_date).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour:'2-digit', minute:'2-digit', hour12:true })} IST
        </span>

        {sold && <span className={styles.soldBadge}>Sold Out</span>}
        {lowStock && !sold && (
          <span className={styles.lowBadge}>{stock.available} available</span>
        )}
      </div>

      <div className={styles.body}>
        <h3 className={styles.name}><button className={styles.detailLink} onClick={e => { e.stopPropagation(); goToEvent(event) }}>{event.name}<span className="visually-hidden"> — view event details</span></button></h3>

        <div className={styles.meta}>
          <span>📍 {event.venue}{(event._city || eventCity(event)) && ` · ${event._city || eventCity(event)}`}</span>
          <span>📅 {formatDate(event.event_date)}</span>
        </div>

        {/* Tier pills */}
        {event.tiers?.length > 0 && (
          <div className={styles.tiers}>
            {event.tiers.slice(0, 3).map(t => (
              <span key={t.id} className={styles.tierPill} style={{ background: t.color + '22', color: 'var(--dark)', borderColor: t.color + '55' }}>
                {t.name}
              </span>
            ))}
          </div>
        )}

        <div className={styles.footer}>
          <div className={styles.priceWrap}>
            <span className={styles.price}>{fmtPrice(displayPrice)}</span>
            <span className={styles.tickets}>{sold ? '— Sold out' : `🎟️ ${stock.available} available`}</span>
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
