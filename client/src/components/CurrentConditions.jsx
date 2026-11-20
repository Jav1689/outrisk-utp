import { CloudSun, Droplet, Droplets, RefreshCw, Sun, Wind } from 'lucide-react'
import { reading, timeLabel, weatherDescription } from '../weather'

export default function CurrentConditions({ conditions, loading, error, retry }) {
  const [description, WeatherIcon] = weatherDescription(conditions?.weather_code, conditions?.is_day)
  const metrics = [
    [Droplet, 'Humidity', reading(conditions?.humidity, '%')],
    [Droplets, conditions?.precipitation_interval_minutes ? `${conditions.precipitation_interval_minutes}-min precip.` : 'Precipitation', reading(conditions?.precipitation, ' mm', 2)],
    [Sun, 'UV index', reading(conditions?.uv_index, '', 1)],
    [Wind, 'Air quality', reading(conditions?.aqi, ' US AQI')],
  ]
  const timestamp = conditions?.datetime

  return (
    <section className="panel conditions" aria-labelledby="conditions-title" aria-busy={loading}>
      <div className="panel-heading">
        <span className="section-icon"><CloudSun size={20} /></span>
        <div><h2 id="conditions-title">Current conditions</h2><p>Weather and air quality at your location</p></div>
      </div>
      {error ? (
        <div className="empty-state" role="status">
          <p>{error}</p><button className="secondary-button" onClick={retry}><RefreshCw size={15} /> Retry</button>
        </div>
      ) : (
        <>
          <div className="temperature-row">
            <div>
              <div className="temperature">{reading(conditions?.temperature, '°')}<span>{conditions?.temperature == null ? '' : 'C'}</span></div>
              <div className="condition-label">{loading ? 'Loading conditions…' : description}</div>
            </div>
            <div className="weather-mark"><WeatherIcon size={43} strokeWidth={1.45} aria-hidden="true" /></div>
          </div>
          <dl className="metric-grid">
            {metrics.map(([Icon, label, value]) => (
              <div key={label}><dt><Icon size={15} />{label}</dt><dd>{value}</dd></div>
            ))}
          </dl>
          {timestamp && <p className="observed">Updated {timeLabel(Number(timestamp.slice(11, 13)), timestamp.slice(14, 16))} MYT</p>}
        </>
      )}
    </section>
  )
}
