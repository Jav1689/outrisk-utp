import { useMemo } from 'react'
import { ChartNoAxesCombined, ChevronDown, RefreshCw } from 'lucide-react'
import { Area, Bar, CartesianGrid, ComposedChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { dateLabel, RISK_COLORS, reading, timeLabel } from '../weather'

const dayLabel = date => dateLabel(date, { weekday: 'short', day: 'numeric', month: 'short' })
const entryRisk = row => row.risk_level || 'Unavailable'

function ForecastTooltip({ active, payload }) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  return (
    <div className="chart-tooltip">
      <strong>{dayLabel(row.datetime)} · {timeLabel(Number(row.datetime.slice(11, 13)))}</strong>
      <p>{reading(row.temperature, '°C', 1)} · {entryRisk(row)}</p>
    </div>
  )
}

function RiskBar({ x, y, width, height, payload }) {
  return <rect x={x} y={y} width={width} height={height} rx={2} fill={RISK_COLORS[entryRisk(payload)]} />
}

export default function ForecastChart({ rows, location, loading, error, retry, onChoose, today }) {
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
          <div><h2 id="forecast-title">7-day risk forecast</h2><p>Hourly outlook for {location} · Malaysia time</p></div>
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
          {hasMissingRisk && <p className="forecast-note">Risk is unavailable where weather or air-quality readings are missing.</p>}
          <div className="forecast-days">
            {Object.entries(days).map(([date, hours]) => {
              const temps = hours.flatMap(row => row.temperature == null ? [] : [row.temperature])
              const safe = hours.filter(row => row.risk_level === 'Safe').length
              const rated = hours.filter(row => row.risk_level).length
              return (
                <details key={date}>
                  <summary>
                    <span>{date === today ? 'Today' : dayLabel(date)}</span>
                    <span>{temps.length ? `${Math.round(Math.min(...temps))}–${Math.round(Math.max(...temps))}°C` : '—'}</span>
                    <span>{rated ? `${safe} low-risk ${safe === 1 ? 'hour' : 'hours'}` : 'Risk unavailable'}</span>
                    <ChevronDown size={17} aria-hidden="true" />
                  </summary>
                  <div className="forecast-hours">
                    {hours.map(row => {
                      const hour = Number(row.datetime.slice(11, 13))
                      return (
                        <button type="button" key={row.datetime} className="forecast-hour" disabled={!row.risk_level} onClick={() => onChoose(date, hour)}>
                          <strong>{timeLabel(hour)}</strong><span>{reading(row.temperature, '°C')}</span>
                          <span className="hour-risk" style={{ color: RISK_COLORS[entryRisk(row)] }}>{entryRisk(row)}</span>
                        </button>
                      )
                    })}
                  </div>
                </details>
              )
            })}
          </div>
        </>
      )}
    </section>
  )
}
