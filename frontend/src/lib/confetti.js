const COLORS = ['#E0122B', '#FF3B5C', '#8B5CF6', '#FCD34D', '#6EE7B7', '#FDBA74', '#FF5A3C']

// Tiny dependency-free confetti burst — fires a canvas overlay of candy-colored
// paper pieces that fall & tumble, then cleans itself up.
export function fireConfetti({ particleCount = 140, duration = 2600 } = {}) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const canvas = document.createElement('canvas')
  canvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:4000;'
  document.body.appendChild(canvas)
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1

  function resize() {
    canvas.width = window.innerWidth * dpr
    canvas.height = window.innerHeight * dpr
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  resize()
  window.addEventListener('resize', resize)

  const W = window.innerWidth
  const particles = Array.from({ length: particleCount }, () => ({
    x: W / 2 + (Math.random() - 0.5) * W * 0.5,
    y: -20 - Math.random() * 120,
    vx: (Math.random() - 0.5) * 6,
    vy: 2 + Math.random() * 4,
    size: 6 + Math.random() * 7,
    rot: Math.random() * 360,
    vrot: (Math.random() - 0.5) * 12,
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
    shape: Math.random() > 0.5 ? 'rect' : 'circle',
    sway: Math.random() * Math.PI * 2,
  }))

  const start = performance.now()
  let raf

  function tick(now) {
    const elapsed = now - start
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
    for (const p of particles) {
      p.vy += 0.05
      p.x += p.vx + Math.sin(p.sway + elapsed / 300) * 0.8
      p.y += p.vy
      p.rot += p.vrot
      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate((p.rot * Math.PI) / 180)
      ctx.fillStyle = p.color
      if (p.shape === 'rect') {
        ctx.fillRect(-p.size / 2, -p.size / 3, p.size, p.size * 0.6)
      } else {
        ctx.beginPath()
        ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.restore()
    }
    if (elapsed < duration) {
      raf = requestAnimationFrame(tick)
    } else {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      canvas.remove()
    }
  }
  raf = requestAnimationFrame(tick)
}
