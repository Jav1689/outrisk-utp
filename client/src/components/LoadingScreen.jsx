import { useEffect, useState } from 'react'
import { Leaf } from 'lucide-react'

export default function LoadingScreen({ onFinished }) {
  const [fading, setFading] = useState(false)

  useEffect(() => {
    // Graceful timer allowing initial assets to hydrate
    const timer = setTimeout(() => setFading(true), 900)
    const exitTimer = setTimeout(() => onFinished(), 1500)
    return () => {
      clearTimeout(timer)
      clearTimeout(exitTimer)
    }
  }, [onFinished])

  return (
    <div className={`loading-screen ${fading ? 'fade-out' : ''}`}>
      <div className="loading-badge">
        <div className="loading-icon-wrap">
          <img src="/outrisk-icon.svg" alt="OutRisk UTP logo" className="loading-logo" width="48" height="48" />
        </div>
        <div className="loading-text">
          <strong>OutRisk UTP</strong>
          <span>Checking clean air & weather…</span>
        </div>
        <div className="loading-bar">
          <div className="loading-bar-fill" />
        </div>
      </div>
    </div>
  )
}
