import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useApp } from '../context/AppContext'
import styles from './Categories.module.css'

gsap.registerPlugin(ScrollTrigger)

const CATS = [
  { id: 'all',     emoji: '✨', label: 'All Events',     grad: 'linear-gradient(135deg,#E0122B,#8B5CF6)' },
  { id: 'Music',   emoji: '🎵', label: 'Music',          grad: 'linear-gradient(135deg,#E0122B,#FF3B5C)' },
  { id: 'Movies',  emoji: '🎬', label: 'Movies',         grad: 'linear-gradient(135deg,#8B5CF6,#7DD3FC)' },
  { id: 'Social',  emoji: '🎉', label: 'Get-togethers',  grad: 'linear-gradient(135deg,#FDBA74,#FCD34D)' },
  { id: 'Festival',emoji: '🎪', label: 'Festivals',      grad: 'linear-gradient(135deg,#FF5A3C,#FCD34D)' },
  { id: 'Sports',  emoji: '🏆', label: 'Sports',         grad: 'linear-gradient(135deg,#22C55E,#6EE7B7)' },
  { id: 'Food',    emoji: '🍔', label: 'Food & Drink',   grad: 'linear-gradient(135deg,#FCD34D,#FF5A3C)' },
  { id: 'Tech',    emoji: '💡', label: 'Tech',           grad: 'linear-gradient(135deg,#7DD3FC,#8B5CF6)' },
  { id: 'Art',     emoji: '🎨', label: 'Art & Culture',  grad: 'linear-gradient(135deg,#8B5CF6,#DDD6FE)' },
  { id: 'Wellness',emoji: '🧘', label: 'Wellness',       grad: 'linear-gradient(135deg,#6EE7B7,#7DD3FC)' },
  { id: 'Comedy',  emoji: '🎤', label: 'Comedy',         grad: 'linear-gradient(135deg,#FF3B5C,#FCD34D)' },
]

export default function Categories() {
  const { category, setCategory } = useApp()
  const secRef = useRef(null)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
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
              aria-pressed={category === id}
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
