import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import styles from './HowItWorks.module.css'

gsap.registerPlugin(ScrollTrigger)

const STEPS = [
  { n: '01', emoji: '🔍', title: 'Browse Events', body: 'Explore concerts, movies, meetups and more from artists and organizers near you.' },
  { n: '02', emoji: '🎟️', title: 'Pick Your Tickets', body: 'Choose a tier and quantity. Availability is checked when you confirm; tickets are not held.' },
  { n: '03', emoji: '🎉', title: 'Enjoy the Moment', body: 'Show up, have a blast, and make memories. That\'s literally the whole plan.' },
]

export default function HowItWorks() {
  const secRef = useRef(null)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const ctx = gsap.context(() => {
      gsap.from('.step-card', {
        scrollTrigger: { trigger: secRef.current, start: 'top 78%' },
        x: -50, opacity: 0,
        stagger: 0.2, duration: 0.7,
        ease: 'power3.out',
      })
    }, secRef)
    return () => ctx.revert()
  }, [])

  return (
    <section ref={secRef} id="how" className={`section ${styles.section}`}>
      {/* Decorative blobs */}
      <div className={`blob blob-pink ${styles.blob1}`} />
      <div className={`blob blob-mint ${styles.blob2}`} />

      <div className="container">
        <div className="section-header">
          <span className="section-eyebrow">The process</span>
          <h2 className="section-title">Booking in <span>3 easy steps</span> 💫</h2>
          <p className="section-subtitle">Browse, choose, and find your confirmed booking in My tickets.</p>
        </div>

        <div className={styles.grid}>
          {STEPS.map(({ n, emoji, title, body }) => (
            <div key={n} className={`step-card ${styles.card}`}>
              <div className={styles.num}>{n}</div>
              <div className={styles.emojiWrap}>{emoji}</div>
              <h3 className={styles.title}>{title}</h3>
              <p className={styles.body}>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
