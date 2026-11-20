import { useEffect, useRef } from 'react'

export default function CustomCursor() {
  const dotRef = useRef(null)
  const ringRef = useRef(null)

  useEffect(() => {
    // Skip on touch devices
    if (window.matchMedia('(pointer: coarse)').matches) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const dot = dotRef.current
    const ring = ringRef.current
    if (!dot || !ring) return

    let mouseX = 0, mouseY = 0
    let ringX = 0, ringY = 0
    let animId

    function onMouseMove(event) {
      mouseX = event.clientX
      mouseY = event.clientY
      dot.style.transform = `translate(${mouseX - 6}px, ${mouseY - 6}px)`
    }

    // Smooth trailing ring using lerp
    function animate() {
      ringX += (mouseX - ringX) * 0.15
      ringY += (mouseY - ringY) * 0.15
      ring.style.transform = `translate(${ringX - 18}px, ${ringY - 18}px)`
      animId = requestAnimationFrame(animate)
    }

    // Scale up on interactive elements
    function onPointerOver(event) {
      if (event.target.closest('button, a, select, input, label, summary')) {
        dot.classList.add('cursor-active')
        ring.classList.add('cursor-active')
      }
    }
    function onPointerOut() {
      dot.classList.remove('cursor-active')
      ring.classList.remove('cursor-active')
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('pointerover', onPointerOver)
    document.addEventListener('pointerout', onPointerOut)
    animId = requestAnimationFrame(animate)

    return () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('pointerover', onPointerOver)
      document.removeEventListener('pointerout', onPointerOut)
      cancelAnimationFrame(animId)
    }
  }, [])

  return (
    <>
      <div ref={dotRef} className="cursor-dot" />
      <div ref={ringRef} className="cursor-ring" />
    </>
  )
}
