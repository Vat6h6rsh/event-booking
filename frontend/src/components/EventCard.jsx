import styles from './EventCard.module.css'
import { useApp } from '../context/AppContext'

const FALLBACK = {
  Music:   'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=600&h=380&q=80',
  Movies:  'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&h=380&q=80',
  Social:  'https://images.unsplash.com/photo-1527529482837-4698179dc6ce?auto=format&fit=crop&w=600&h=380&q=80',
  Festival:'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?auto=format&fit=crop&w=600&h=380&q=80',
  default: 'https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&h=380&q=80',
}

const CAT_BADGE = {
  Music:   'badge-music',
  Movies:  'badge-movies',
  Social:  'badge-social',
  Festival:'badge-other',
}

function fmt(iso) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

function fmtPrice(p) {
  if (!p) return 'Free'
  return `₹${(p).toLocaleString('en-IN')}`
}

export default function EventCard({ event }) {
  const { openBooking } = useApp()
  const img = event.image_url || FALLBACK[event.category] || FALLBACK.default
  const sold = event.available_tickets === 0

  return (
    <article className={`card ${styles.card}`}>
      {/* Image */}
      <div className={styles.imgWrap}>
        <img src={img} alt={event.name} loading="lazy" />
        <span className={`badge ${CAT_BADGE[event.category] || 'badge-other'} ${styles.catBadge}`}>
          {event.category}
        </span>
        {sold && <span className={styles.soldBadge}>Sold Out</span>}
      </div>

      {/* Body */}
      <div className={styles.body}>
        <h3 className={styles.name}>{event.name}</h3>

        <div className={styles.meta}>
          <span>📍 {event.venue}</span>
          <span>📅 {fmt(event.event_date)}</span>
        </div>

        <div className={styles.footer}>
          <div className={styles.priceWrap}>
            <span className={styles.price}>{fmtPrice(event.price)}</span>
            <span className={styles.tickets}>
              🎟️ {event.available_tickets} left
            </span>
          </div>
          <button
            className={`btn btn-primary btn-sm ${sold ? styles.soldBtn : ''}`}
            onClick={() => openBooking(event)}
            disabled={sold}
          >
            {sold ? 'Sold Out' : 'Book Now →'}
          </button>
        </div>
      </div>
    </article>
  )
}
