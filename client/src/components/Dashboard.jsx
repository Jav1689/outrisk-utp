import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { ArrowUpRight, Clock3, Compass, FlaskConical, MapPin } from 'lucide-react'
import { errorMessage, getCurrentWeather, getForecastRisk, getRecommendations, predictRisk } from '../api/client'
import { addDays, dateLabel, FORECAST_DAYS, LOCATIONS, malaysiaNow } from '../weather'
import ActivityForm from './ActivityForm'
import CurrentConditions from './CurrentConditions'
import Recommendations from './Recommendations'
import RiskResult from './RiskResult'

const ForecastChart = lazy(() => import('./ForecastChart'))
const emptyReading = { data: null, error: '' }

export default function Dashboard() {
  const [selection, setSelection] = useState(() => ({ location: 'UTP', activity: 'jogging', ...malaysiaNow() }))
  const [source, setSource] = useState('live')
  const [requestNumber, setRequestNumber] = useState(0)
  const [readings, setReadings] = useState(null)
  const [assessment, setAssessment] = useState(null)
  const [formError, setFormError] = useState('')
  const [checking, setChecking] = useState(false)
  const activeCheck = useRef(null)
  const resultAnchor = useRef(null)
  const { date: today } = malaysiaNow()
  const location = selection.location
  const requestKey = `${location}/${source}/${requestNumber}`

  useEffect(() => {
    const controller = new AbortController()
    function receive(name, value) {
      if (controller.signal.aborted) return
      setReadings(previous => ({ ...(previous?.key === requestKey ? previous : { key: requestKey }), [name]: value }))
    }
    getCurrentWeather(location, source, controller.signal).then(
      payload => receive('current', { data: payload.current }),
      error => receive('current', { error: errorMessage(error) }),
    )
    getForecastRisk(location, source, controller.signal).then(
      rows => receive('forecast', { data: rows }),
      error => receive('forecast', { error: errorMessage(error) }),
    )
    return () => controller.abort()
  }, [location, source, requestKey])

  useEffect(() => () => activeCheck.current?.abort(), [])
  useEffect(() => {
    if (assessment) resultAnchor.current?.focus({ preventScroll: true })
  }, [assessment])

  const current = (readings?.key === requestKey && readings.current) || emptyReading
  const forecast = (readings?.key === requestKey && readings.forecast) || emptyReading
  const unavailable = Boolean(current.error || forecast.error)
  const status = source === 'sample' ? 'Sample data' : unavailable ? 'Data unavailable' : current.data ? 'Live weather' : 'Connecting'

  function clearAssessment() {
    activeCheck.current?.abort()
    setChecking(false)
    setFormError('')
    setAssessment(null)
  }

  function change(field, value) {
    clearAssessment()
    setSelection(previous => ({ ...previous, [field]: value }))
  }

  function switchSource(value) {
    clearAssessment()
    setSource(value)
  }

  async function check(nextSelection) {
    clearAssessment()
    const controller = new AbortController()
    activeCheck.current = controller
    setChecking(true)
    try {
      const input = { ...nextSelection, source }
      const [prediction, recommendations] = await Promise.all([
        predictRisk(input, controller.signal), getRecommendations(input, controller.signal),
      ])
      if (!controller.signal.aborted) setAssessment({ prediction, recommendations })
    } catch (error) {
      if (!controller.signal.aborted) setFormError(errorMessage(error))
      controller.abort()
    } finally {
      if (activeCheck.current === controller) setChecking(false)
    }
  }

  function chooseHour(date, hour) {
    clearAssessment()
    setSelection(previous => ({ ...previous, date, hour }))
    document.getElementById('planner')?.scrollIntoView({ block: 'center' })
  }

  const retry = () => setRequestNumber(previous => previous + 1)

  return (
    <>
      <a className="skip-link" href="#overview">Skip to dashboard</a>
      <header className="site-header">
        <div className="header-inner">
          <a className="brand" href="#overview"><span className="brand-icon"><Compass size={24} strokeWidth={1.8} /></span>OutRisk <span>UTP</span></a>
          <nav aria-label="Main navigation"><a href="#overview">Overview</a><a href="#forecast">Forecast</a></nav>
          <div className="timezone"><Clock3 size={15} /><span>Malaysia time</span><span className="zone-offset">UTC+8</span></div>
        </div>
      </header>
      <main id="overview">
        <section className="hero" aria-labelledby="page-title">
          <div className="hero-copy">
            <p className="hero-region"><MapPin size={16} /> PERAK, MALAYSIA</p>
            <h1 id="page-title">Plan your time outdoors</h1>
            <p className="hero-description">Check local weather and outdoor activity risk for UTP and Seri Iskandar.</p>
          </div>
        </section>
        <div className="location-bar">
          <div className="location-control">
            <span className="location-label"><MapPin size={17} /> Location</span>
            <div className="segmented" role="group" aria-label="Forecast location">
              {Object.keys(LOCATIONS).map(value => (
                <button key={value} aria-pressed={value === location} onClick={() => change('location', value)}>{value}</button>
              ))}
            </div>
          </div>
          <div className="location-meta">
            <span className="today">{dateLabel(today, { weekday: 'long', day: 'numeric', month: 'short' })}</span>
            <span className={`status ${source === 'sample' || unavailable ? 'status-muted' : ''}`} role="status"><i />{status}</span>
          </div>
        </div>
        {(source === 'sample' || unavailable) && (
          <div className="source-notice">
            <span><FlaskConical size={18} /> {source === 'sample' ? 'Sample weather is for exploring the dashboard.' : 'Live weather is temporarily unavailable.'}</span>
            <button className="secondary-button" onClick={() => switchSource(source === 'sample' ? 'live' : 'sample')}>
              {source === 'sample' ? 'Return to live weather' : 'Explore sample weather'}
            </button>
          </div>
        )}
        <div className="dashboard-grid">
          <CurrentConditions conditions={current.data} loading={!current.data && !current.error} error={current.error} retry={retry} />
          <ActivityForm selection={selection} onChange={change} onSubmit={event => { event.preventDefault(); check(selection) }}
            loading={checking} error={formError} minDate={today} maxDate={addDays(today, FORECAST_DAYS - 1)} />
        </div>
        {assessment && (
          <div className="dashboard-grid assessment" ref={resultAnchor} tabIndex={-1} aria-label="Activity risk and recommendations">
            <RiskResult prediction={assessment.prediction} />
            <Recommendations data={assessment.recommendations} onTryTime={hour => {
              const next = { ...selection, hour }
              setSelection(next)
              check(next)
            }} />
          </div>
        )}
        <Suspense fallback={<section className="panel forecast chart-loading" id="forecast" role="status">Loading forecast…</section>}>
          <ForecastChart key={requestKey} rows={forecast.data || []} location={location} loading={!forecast.data && !forecast.error}
            error={forecast.error} retry={retry} onChoose={chooseHour} today={today} />
        </Suspense>
      </main>
      <footer>
        <div><strong>OutRisk UTP</strong><p>Use these estimates for planning and check official alerts before heading out.</p></div>
        <div><a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo <ArrowUpRight size={15} /></a>
          <a href="https://atmosphere.copernicus.eu/" target="_blank" rel="noreferrer">Copernicus CAMS <ArrowUpRight size={15} /></a>
          <a href="https://www.met.gov.my/" target="_blank" rel="noreferrer">MET Malaysia <ArrowUpRight size={15} /></a></div>
      </footer>
    </>
  )
}
