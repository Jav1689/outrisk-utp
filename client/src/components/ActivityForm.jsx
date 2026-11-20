import { CalendarDays, ChevronDown, Clock3, LoaderCircle, MapPin, PersonStanding, ShieldCheck } from 'lucide-react'
import { ACTIVITIES, LOCATIONS, timeLabel } from '../weather'

function Field({ label, icon: Icon, children, select = false }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <span className="field-input">
        <Icon size={17} aria-hidden="true" />
        {children}
        {select && <ChevronDown className="field-chevron" size={16} aria-hidden="true" />}
      </span>
    </label>
  )
}

export default function ActivityForm({ selection, onChange, onSubmit, loading, error, minDate, maxDate }) {
  return (
    <section className="panel activity" aria-labelledby="activity-title" id="planner">
      <div className="panel-heading">
        <span className="section-icon"><CalendarDays size={20} /></span>
        <div><h2 id="activity-title">Plan an activity</h2><p>Check the forecast for your chosen time</p></div>
      </div>
      <form onSubmit={onSubmit} aria-busy={loading}>
        <div className="form-grid">
          <Field label="Location" icon={MapPin} select>
            <select value={selection.location} onChange={event => onChange('location', event.target.value)}>
              {Object.keys(LOCATIONS).map(location => <option key={location}>{location}</option>)}
            </select>
          </Field>
          <Field label="Activity" icon={PersonStanding} select>
            <select value={selection.activity} onChange={event => onChange('activity', event.target.value)}>
              {Object.entries(ACTIVITIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </Field>
          <Field label="Date" icon={CalendarDays}>
            <input type="date" required min={minDate} max={maxDate} value={selection.date} onChange={event => onChange('date', event.target.value)} />
          </Field>
          <Field label="Time (MYT)" icon={Clock3} select>
            <select value={selection.hour} onChange={event => onChange('hour', Number(event.target.value))}>
              {Array.from({ length: 24 }, (_, hour) => <option key={hour} value={hour}>{timeLabel(hour)}</option>)}
            </select>
          </Field>
        </div>
        <button className="primary-button" disabled={loading} type="submit">
          {loading ? <LoaderCircle size={19} className="spin" /> : <ShieldCheck size={19} />}
          {loading ? 'Checking risk…' : 'Check risk'}
        </button>
        {error && <p className="form-error" role="alert">{error}</p>}
      </form>
    </section>
  )
}
