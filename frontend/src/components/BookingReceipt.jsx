import { formatMoney } from '../lib/money'
import { formatDate } from '../lib/booking'
import styles from './BookingReceipt.module.css'
export default function BookingReceipt({ booking, event, fresh = true }) {
  return <section className={styles.receipt} aria-label={`Booking ${booking.id}`}>
    <h3>{booking.status === 'confirmed' ? 'Booking confirmed' : `Booking ${booking.status}`}</h3>
    <p>Booking #{booking.id} · <strong>{booking.status}</strong></p>
    <h4>{event?.name || booking.event_name || `Event #${booking.event_id}`}</h4>
    <p>{formatDate(event?.event_date)}</p><p>{event?.venue || 'Venue unavailable'}</p>
    <dl className={styles.facts}><div><dt>Tier</dt><dd>{booking.tier_name || event?.tiers?.find(t => t.id === booking.tier_id)?.name || (booking.tier_id ? `Tier #${booking.tier_id}` : 'General admission')}</dd></div><div><dt>Quantity</dt><dd>{booking.quantity}</dd></div><div><dt>Recorded total</dt><dd>{formatMoney(booking.total_price)}</dd></div></dl>
    <p>No payment was collected in this demo.</p>
    {fresh && booking.status === 'confirmed' && <p>A confirmation email is on its way, sent in the background. Your booking is confirmed independently of email delivery.</p>}
    <h4>Ticket codes{booking.status === 'cancelled' && ' — VOID'}</h4><ul className={styles.codes}>{booking.attendees?.map(a => <li key={a.id || a.ticket_code}><span>{a.full_name}</span> {booking.status === 'cancelled' ? <strong>Void — invalid for admission</strong> : <code>{a.ticket_code}</code>}</li>)}</ul>
    {!booking.attendees?.length && <p>No ticket codes recorded.</p>}
  </section>
}
