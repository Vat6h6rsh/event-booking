import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useApp } from '../context/AppContext'
import EventCard from './EventCard'
import styles from './EventsSection.module.css'

gsap.registerPlugin(ScrollTrigger)

export default function EventsSection() {
  const { events, eventsLoading, category } = useApp()
  const secRef = useRef(null)
  const prevLenRef = useRef(0)

  const filtered = category === 'all'
    ? events
    : events.filter((e) => e.category === category)

  useEffect(() => {
    if (filtered.length === 0 || filtered.length === prevLenRef.current) return
    prevLenRef.current = filtered.length

    const ctx = gsap.context(() => {
      gsap.from('.ev-card', {
        scrollTrigger: { trigger: secRef.current, start: 'top 82%', once: true },
        y: 60, opacity: 0,
        stagger: 0.1, duration: 0.7,
        ease: 'power3.out',
      })
    }, secRef)
    return () => ctx.revert()
  }, [filtered.length])

  return (
    <section ref={secRef} id="events" className={`section ${styles.section}`}>
      <div className="container">
        <div className="section-header">
          <span className="section-eyebrow">Live &amp; Upcoming</span>
          <h2 className="section-title">What's on <span>right now</span> 🎪</h2>
          <p className="section-subtitle">
            Browse and book — your next big night out is one tap away.
          </p>
        </div>

        {eventsLoading ? (
          <div className={styles.loading}>
            <div className="spinner" />
            <p>Loading amazing events…</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className={styles.empty}>
            <span>🥺</span>
            <p>No events in this category yet!</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {filtered.map((ev) => (
              <div key={ev.id} className={`ev-card ${styles.cardWrap}`}>
                <EventCard event={ev} />
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
