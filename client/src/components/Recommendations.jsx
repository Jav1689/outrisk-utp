import { Clock3, Lightbulb } from 'lucide-react'
import { timeLabel } from '../weather'

export default function Recommendations({ data, onTryTime }) {
  return (
    <section className="panel recommendations" aria-labelledby="recommendations-title">
      <div className="panel-heading">
        <span className="section-icon"><Lightbulb size={20} /></span>
        <div><h2 id="recommendations-title">Recommendations</h2><p>{data.advice}</p></div>
      </div>
      <h3>Precautions</h3>
      <ul>{data.precautions.map(precaution => <li key={precaution}>{precaution}</li>)}</ul>
      <h3>Alternative times</h3>
      {data.alternative_times.length > 0 ? (
        <div className="time-list">
          {data.alternative_times.map(({ datetime, hour, note }) => (
            <button key={datetime} onClick={() => onTryTime(hour)} title={note}>
              <Clock3 size={15} /> {timeLabel(hour)}
            </button>
          ))}
        </div>
      ) : <p className="muted">No other low-risk hours remain on this date.</p>}
      {data.alternative_activities.length > 0 && <p className="alternatives"><strong>Other options</strong> {data.alternative_activities.join(' · ')}</p>}
    </section>
  )
}
