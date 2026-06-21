import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useApp } from '../context/AppContext'
import styles from './Categories.module.css'

gsap.registerPlugin(ScrollTrigger)

const CATS = [
  { id: 'all',    emoji: '✨', label: 'All Events',     grad: 'linear-gradient(135deg,#FF6B9D,#A78BFA)' },
  { id: 'Music',  emoji: '🎵', label: 'Music',           grad: 'linear-gradient(135deg,#FF6B9D,#FF8C69)' },
  { id: 'Movies', emoji: '🎬', label: 'Movies',          grad: 'linear-gradient(135deg,#A78BFA,#7DD3FC)' },
  { id: 'Social', emoji: '🎉', label: 'Get-togethers',   grad: 'linear-gradient(135deg,#FDBA74,#FCD34D)' },
  { id: 'Festival',emoji:'🎪', label: 'Festivals',       grad: 'linear-gradient(135deg,#6EE7B7,#7DD3FC)' },
  { id: 'Other',  emoji: '🎭', label: 'Theater & More',  grad: 'linear-gradient(135deg,#DDD6FE,#A78BFA)' },
]

export default function Categories() {
  const { category, setCategory } = useApp()
  const secRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.cat-card', {
        scrollTrigger: { trigger: secRef.current, start: 'top 80%' },
        scale: 0.75, opacity: 0,
        stagger: 0.08, duration: 0.55,
        ease: 'back.out(1.8)',
      })
    }, secRef)
    return () => ctx.revert()
  }, [])

  return (
    <section ref={secRef} className={`section ${styles.section}`}>
      <div className="container">
        <div className="section-header">
          <span className="section-eyebrow">Browse</span>
          <h2 className="section-title">Pick your <span>vibe</span> 🌟</h2>
        </div>

        <div className={styles.grid}>
          {CATS.map(({ id, emoji, label, grad }) => (
            <button
              key={id}
              className={`cat-card ${styles.card} ${category === id ? styles.active : ''}`}
              onClick={() => setCategory(id)}
              style={{ '--cat-grad': grad }}
            >
              <span className={styles.emoji}>{emoji}</span>
              <span className={styles.label}>{label}</span>
              {category === id && <span className={styles.tick}>✓</span>}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
