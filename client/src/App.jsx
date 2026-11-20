import { useState } from 'react'
import Dashboard from './components/Dashboard.jsx'
import ThreeBackground from './components/ThreeBackground.jsx'
import CustomCursor from './components/CustomCursor.jsx'
import LoadingScreen from './components/LoadingScreen.jsx'

export default function App() {
  const [loading, setLoading] = useState(true)

  return (
    <>
      <ThreeBackground />
      <CustomCursor />
      {loading && <LoadingScreen onFinished={() => setLoading(false)} />}
      <Dashboard />
    </>
  )
}
