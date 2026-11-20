import { ShieldCheck, ShieldAlert, TriangleAlert } from 'lucide-react'
import { ACTIVITIES, dateLabel, RISK_COLORS, timeLabel } from '../weather'

const ICONS = { Safe: ShieldCheck, Caution: TriangleAlert, Hazardous: ShieldAlert }

export default function RiskResult({ prediction }) {
  const Icon = ICONS[prediction.risk_level]
  const color = RISK_COLORS[prediction.risk_level]
  return (
    <section className="panel result" aria-labelledby="result-title">
      <div className="panel-heading">
        <span className="section-icon"><ShieldCheck size={20} /></span>
        <div><h2 id="result-title">Risk assessment</h2><p>{ACTIVITIES[prediction.activity]} · {prediction.location}</p></div>
      </div>
      <div className={`risk-card ${prediction.risk_level.toLowerCase()}`}>
        <Icon size={28} aria-hidden="true" />
        <div><strong>{prediction.risk_level}</strong><p>{dateLabel(prediction.date, { weekday: 'short', day: 'numeric', month: 'short' })} · {timeLabel(prediction.hour)} MYT</p></div>
        <span>{prediction.confidence}% model confidence</span>
      </div>
      {prediction.factors.length > 0 && <p className="factor-list">{prediction.factors.join(' · ')}</p>}
      <dl className="probabilities">
        {Object.entries(prediction.probabilities).map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt><dd>{value}%</dd>
            <div className="track" aria-hidden="true"><span style={{ width: `${value}%`, backgroundColor: RISK_COLORS[label] || color }} /></div>
          </div>
        ))}
      </dl>
    </section>
  )
}
