import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { useApp } from '../context/AppContext'
import styles from './Hero.module.css'

const HERO_IMGS = [
  'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=400&h=300&q=80',
  'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=400&h=300&q=80',
  'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=400&h=300&q=80',
  'https://images.unsplash.com/photo-1527529482837-4698179dc6ce?auto=format&fit=crop&w=400&h=300&q=80',
]

export default function Hero({ onExplore }) {
  const { setAuthOpen, user } = useApp()
  const heroRef = useRef(null)
  const tlRef   = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      tlRef.current = gsap.timeline({ defaults: { ease: 'power3.out' } })
        .from('.hero-eyebrow', { y: 24, opacity: 0, duration: 0.6 })
        .from('.hero-word',    { y: 56, opacity: 0, stagger: 0.08, duration: 0.8 }, '-=0.3')
        .from('.hero-sub',     { y: 24, opacity: 0, duration: 0.6 }, '-=0.4')
        .from('.hero-ctas',    { y: 20, opacity: 0, scale: 0.96, duration: 0.5 }, '-=0.35')
        .from('.hero-stats',   { y: 16, opacity: 0, stagger: 0.1, duration: 0.5 }, '-=0.3')
        .from('.hero-img',     { scale: 1.08, opacity: 0, stagger: 0.12, duration: 0.7 }, '-=0.7')
        .from('.hero-float',   { y: 16, opacity: 0, stagger: 0.15, duration: 0.4 }, '-=0.5')
    }, heroRef)
    return () => ctx.revert()
  }, [])

  return (
    <section ref={heroRef} className={styles.hero}>
      {/* Decorative blobs */}
      <div className={`blob blob-pink ${styles.blob1}`} />
      <div className={`blob blob-purple ${styles.blob2}`} />
      <div className={`blob blob-yellow ${styles.blob3}`} />

      <div className={`container ${styles.inner}`}>
        {/* ── Left col ── */}
        <div className={styles.content}>
          <span className={`hero-eyebrow ${styles.eyebrow}`}>
            ✨ India's Cutest Event Platform
          </span>

          <h1 className={styles.title}>
            {'Your next'.split(' ').map((w, i) => (
              <span key={i} className={`hero-word ${styles.word}`}>{w}&nbsp;</span>
            ))}
            <br />
            {'adventure'.split('').map((c, i) => (
              <span key={i} className={`hero-word ${styles.word} ${styles.gradientWord}`}>{c}</span>
            ))}
            <span className={`hero-word ${styles.word}`}>&nbsp;awaits ✨</span>
          </h1>

          <p className={`hero-sub ${styles.subtitle}`}>
            Discover concerts, movie nights, festivals &amp; get-togethers near you.
            Book in seconds, memories forever.
          </p>

          <div className={`hero-ctas ${styles.ctas}`}>
            <button className="btn btn-primary btn-lg" onClick={onExplore}>
              Explore Events 🎪
            </button>
            {!user && (
              <button className="btn btn-secondary btn-lg" onClick={() => setAuthOpen(true)}>
                Sign up free
              </button>
            )}
          </div>

          <div className={styles.stats}>
            {[
              { num: '1,200+', label: 'Events' },
              { num: '50K+',  label: 'Happy fans' },
              { num: '80+',   label: 'Cities' },
            ].map(({ num, label }) => (
              <div key={label} className={`hero-stats ${styles.stat}`}>
                <strong>{num}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Right col: image grid ── */}
        <div className={styles.imgGrid}>
          {HERO_IMGS.map((src, i) => (
            <div key={src} className={`hero-img ${styles.imgWrap} ${i === 1 || i === 3 ? styles.imgShifted : ''}`}>
              <img src={src} alt="" loading="lazy" />
            </div>
          ))}

          {/* Floating stickers */}
          <div className={`hero-float float ${styles.sticker1}`}>🎵</div>
          <div className={`hero-float float-slow ${styles.sticker2}`}>🎟️</div>
          <div className={`hero-float float-fast ${styles.sticker3}`}>⭐</div>
          <div className={`hero-float float ${styles.sticker4}`}>🎉</div>
        </div>
      </div>

      {/* Wave divider */}
      <svg className={styles.wave} viewBox="0 0 1440 80" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
        <path d="M0,40 C360,80 1080,0 1440,40 L1440,80 L0,80 Z" fill="var(--offwhite)" />
      </svg>
    </section>
  )
}
