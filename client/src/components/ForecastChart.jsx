import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { ChartNoAxesCombined, ChevronDown, RefreshCw, X } from 'lucide-react'
import { Area, Bar, CartesianGrid, ComposedChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ACTIVITIES, dateLabel, RISK_COLORS, reading, timeLabel, malaysiaNow } from '../weather'

const dayLabel = date => dateLabel(date, { weekday: 'short', day: 'numeric', month: 'short' })
const entryRisk = row => row.risk_level || 'Unavailable'

function ForecastTooltip({ active, payload }) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  return (
    <div className="chart-tooltip">
      <strong>{dayLabel(row.datetime)} · {timeLabel(Number(row.datetime.slice(11, 13)))}</strong>
      <p>{reading(row.temperature, '°C', 1)} · {entryRisk(row)}</p>
      {row.apparent_temperature != null && <p>Feels like {reading(row.apparent_temperature, '°C', 1)}</p>}
      {row.factors?.length > 0 && <p>{row.factors.join(' · ')}</p>}
    </div>
  )
}

function RiskBar({ x, y, width, height, payload }) {
  return <rect x={x} y={y} width={width} height={height} rx={2} fill={RISK_COLORS[entryRisk(payload)]} />
}

export default function ForecastChart({ rows, location, activity, loading, error, retry, onChoose, today }) {
  const [openDates, setOpenDates] = useState(() => new Set([today]))
  const [activeModalRow, setActiveModalRow] = useState(null)
  const [modalDate, setModalDate] = useState('')
  const [initialTime] = useState(() => malaysiaNow())

  function toggleDate(date) {
    setOpenDates(prev => {
      const next = new Set(prev)
      next.has(date) ? next.delete(date) : next.add(date)
      return next
    })
  }

  function openModal(row, date) {
    setActiveModalRow(row)
    setModalDate(date)
  }

  function closeModal() {
    setActiveModalRow(null)
  }

  useEffect(() => {
    if (!activeModalRow) return
    function handleKeyDown(e) {
      if (e.key === 'Escape') closeModal()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeModalRow])

  const hasMissingRisk = rows.some(row => !row.risk_level)
  const { points, ticks, days } = useMemo(() => {
    const days = {}
    for (const row of rows) (days[row.datetime.slice(0, 10)] ??= []).push(row)
    const points = rows.filter(row => Number(row.datetime.slice(11, 13)) % 3 === 0).map(row => ({ ...row, band: 1 }))
    const ticks = points.filter(row => row.datetime.slice(11, 13) === '12').map(row => row.datetime)
    return { points, ticks, days }
  }, [rows])

  return (
    <section className="panel forecast" id="forecast" aria-labelledby="forecast-title" aria-busy={loading}>
      <div className="forecast-heading">
        <div className="panel-heading">
          <span className="section-icon"><ChartNoAxesCombined size={20} /></span>
          <div><h2 id="forecast-title">7-day risk forecast</h2><p>{ACTIVITIES[activity]} · {location} · Malaysia time</p></div>
        </div>
        <div className="legend" aria-label="Chart legend">
          {Object.entries(RISK_COLORS).slice(0, hasMissingRisk ? 4 : 3).map(([level, color]) => (
            <span key={level}><i style={{ backgroundColor: color }} />{level}</span>
          ))}
        </div>
      </div>
      {loading && <div className="chart-loading" role="status">Loading forecast…</div>}
      {error && <div className="empty-state" role="status"><p>{error}</p><button className="secondary-button" onClick={retry}><RefreshCw size={15} /> Retry</button></div>}
      {points.length > 0 && (
        <>
          <div className="chart-frame" aria-label="Temperature trend and risk estimates at three-hour intervals">
            <ResponsiveContainer width="100%" height={235} minWidth={0}>
              <ComposedChart data={points} margin={{ top: 12, right: 8, bottom: 5, left: 0 }}>
                <defs><linearGradient id="temperature-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#409475" stopOpacity={0.25} /><stop offset="100%" stopColor="#409475" stopOpacity={0.025} /></linearGradient></defs>
                <CartesianGrid vertical={false} stroke="#e5ece7" />
                <XAxis dataKey="datetime" ticks={ticks} tickFormatter={value => dateLabel(value, { weekday: 'short' })} interval={0} tickLine={false} axisLine={false} tickMargin={12} tick={{ fill: '#526a5e', fontSize: 12 }} />
                <YAxis yAxisId="temperature" width={42} domain={['dataMin - 2', 'dataMax + 2']} tickCount={5} axisLine={false} tickLine={false} tickFormatter={value => `${value}°`} tick={{ fill: '#526a5e', fontSize: 12 }} />
                <YAxis yAxisId="risk" hide domain={[0, 13]} />
                <Tooltip content={<ForecastTooltip />} />
                <Area yAxisId="temperature" type="monotone" dataKey="temperature" stroke="#247553" strokeWidth={2.5} fill="url(#temperature-fill)" isAnimationActive={false} />
                <Bar yAxisId="risk" dataKey="band" shape={RiskBar} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          {hasMissingRisk && <p className="forecast-note">Unavailable hours have missing weather or air-quality readings.</p>}
          <div className="forecast-days">
            {Object.entries(days).map(([date, hours]) => {
              const temps = hours.flatMap(row => row.temperature == null ? [] : [row.temperature])
              const safe = hours.filter(row => row.risk_level === 'Safe').length
              const rated = hours.filter(row => row.risk_level).length
              const isOpen = openDates.has(date)
              return (
                <div key={date} className={`forecast-day-accordion ${isOpen ? 'open' : ''}`}>
                  <button
                    type="button"
                    className="forecast-day-header"
                    onClick={() => toggleDate(date)}
                    aria-expanded={isOpen}
                  >
                    <span>{date === today ? 'Today' : dayLabel(date)}</span>
                    <span>{temps.length ? `${Math.round(Math.min(...temps))}–${Math.round(Math.max(...temps))}°C` : '—'}</span>
                    <span>{rated ? `${safe} low-risk ${safe === 1 ? 'hour' : 'hours'}` : 'Risk unavailable'}</span>
                    <ChevronDown size={17} className="accordion-chevron" aria-hidden="true" />
                  </button>
                  <div className="forecast-accordion-body">
                    <div className="forecast-accordion-content">
                      <div className="forecast-hours">
                        {hours.map(row => {
                          const hour = Number(row.datetime.slice(11, 13))
                          const isPast =
                            date < initialTime.date ||
                            (date === initialTime.date && hour < initialTime.hour)
                          const isDisabled = !row.risk_level || isPast

                          return (
                            <button
                              type="button"
                              key={row.datetime}
                              className={`forecast-hour ${isPast ? 'forecast-hour-past' : ''}`}
                              disabled={isDisabled}
                              onClick={() => openModal(row, date)}
                              title={isPast ? 'Time has passed' : ''}
                            >
                              <strong>{timeLabel(hour)}</strong><span>{reading(row.temperature, '°C')}</span>
                              <span className="hour-risk" style={{
                                color: isPast ? '#8a9991' : RISK_COLORS[entryRisk(row)],
                                backgroundColor: entryRisk(row) == "Safe" & !isPast ? "#23805d" : "transparent",
                                height: "20px",
                                width: "36px",
                                textAlign: "center",
                                margin: 0,
                                borderRadius: "8px",
                              }}>
                                {isPast ? 'Passed' : entryRisk(row)}
                              </span>
                              {row.factors?.length > 0 && <span className="hour-factor" title={row.factors.join(' · ')}>{row.factors[0]}</span>}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
      {activeModalRow && createPortal(
        <div
          className="modal-backdrop"
          onClick={e => {
            if (e.target === e.currentTarget) closeModal()
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-time-title"
        >
          <div className="modal-dialog">
            <button
              type="button"
              className="modal-close-btn"
              onClick={closeModal}
              aria-label="Close dialog"
            >
              <X size={18} />
            </button>

            <div className="modal-header">
              <h3 id="modal-time-title">
                {dayLabel(modalDate)} · {timeLabel(Number(activeModalRow.datetime.slice(11, 13)))}
              </h3>
              <span
                className="modal-risk-pill"
                style={{ backgroundColor: `${RISK_COLORS[entryRisk(activeModalRow)]}20`, color: RISK_COLORS[entryRisk(activeModalRow)] }}
              >
                {entryRisk(activeModalRow)} Risk
              </span>
            </div>

            <div className="modal-metrics-grid">
              <div>
                <span>Temperature</span>
                <strong>{reading(activeModalRow.temperature, '°C', 1)}</strong>
              </div>
              <div>
                <span>Feels Like</span>
                <strong>{reading(activeModalRow.apparent_temperature, '°C', 1)}</strong>
              </div>
              <div>
                <span>Precipitation</span>
                <strong>{reading(activeModalRow.precipitation, 'mm', 1)}</strong>
              </div>
              <div>
                <span>UV Index</span>
                <strong>{reading(activeModalRow.uv_index, '', 1)}</strong>
              </div>
              <div>
                <span>Wind Speed</span>
                <strong>{reading(activeModalRow.wind_speed, 'km/h', 1)}</strong>
              </div>
              <div>
                <span>Air Quality (AQI)</span>
                <strong>{reading(activeModalRow.aqi, '', 0)}</strong>
              </div>
            </div>

            {activeModalRow.factors?.length > 0 && (
              <div className="modal-factors">
                <span>Contributing Factors:</span>
                <p>{activeModalRow.factors.join(' · ')}</p>
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="primary-button modal-select-btn"
                onClick={() => {
                  onChoose(modalDate, Number(activeModalRow.datetime.slice(11, 13)))
                  closeModal()
                }}
              >
                Plan for this hour
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </section>
  )
}
