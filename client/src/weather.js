import { Cloud, CloudDrizzle, CloudFog, CloudLightning, CloudRain, CloudSnow, CloudSun, Moon, Sun } from 'lucide-react'

export const LOCATIONS = {
  UTP: 'Universiti Teknologi PETRONAS',
  'Seri Iskandar': 'Seri Iskandar, Perak',
}
export const ACTIVITIES = {
  jogging: 'Jogging',
  cycling: 'Cycling',
  walking: 'Walking',
  sports: 'Outdoor sports',
  commuting: 'Commuting',
}
export const RISK_COLORS = { Safe: '#23805d', Caution: '#ad650a', Hazardous: '#bf4545', Unavailable: '#8a9991' }
export const FORECAST_DAYS = 7
const clock = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Kuala_Lumpur', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', hourCycle: 'h23',
})

export function malaysiaNow() {
  const parts = Object.fromEntries(clock.formatToParts(new Date()).map(({ type, value }) => [type, value]))
  return { date: `${parts.year}-${parts.month}-${parts.day}`, hour: Number(parts.hour) }
}

export function addDays(date, days) {
  const instant = new Date(`${date}T00:00:00Z`)
  instant.setUTCDate(instant.getUTCDate() + days)
  return instant.toISOString().slice(0, 10)
}

export function dateLabel(date, options) {
  return new Intl.DateTimeFormat('en-MY', { ...options, timeZone: 'UTC' }).format(new Date(`${date.slice(0, 10)}T00:00:00Z`))
}

export function timeLabel(hour, minutes = '00') {
  return `${hour % 12 || 12}:${minutes} ${hour < 12 ? 'AM' : 'PM'}`
}

export function reading(value, unit = '', decimals = 0) {
  return value == null ? '—' : `${Number(value.toFixed(decimals))}${unit}`
}

const WEATHER = {
  0: ['Clear sky', Sun], 1: ['Mainly clear', Sun], 2: ['Partly cloudy', CloudSun], 3: ['Overcast', Cloud],
  45: ['Fog', CloudFog], 48: ['Freezing fog', CloudFog],
  51: ['Light drizzle', CloudDrizzle], 53: ['Moderate drizzle', CloudDrizzle], 55: ['Heavy drizzle', CloudDrizzle],
  56: ['Light freezing drizzle', CloudDrizzle], 57: ['Heavy freezing drizzle', CloudDrizzle],
  61: ['Light rain', CloudRain], 63: ['Moderate rain', CloudRain], 65: ['Heavy rain', CloudRain],
  66: ['Light freezing rain', CloudRain], 67: ['Heavy freezing rain', CloudRain],
  71: ['Light snow', CloudSnow], 73: ['Moderate snow', CloudSnow], 75: ['Heavy snow', CloudSnow], 77: ['Snow grains', CloudSnow],
  80: ['Light showers', CloudRain], 81: ['Moderate showers', CloudRain], 82: ['Heavy showers', CloudRain],
  85: ['Light snow showers', CloudSnow], 86: ['Heavy snow showers', CloudSnow],
  95: ['Thunderstorm', CloudLightning], 96: ['Thunderstorm with hail', CloudLightning], 99: ['Thunderstorm with heavy hail', CloudLightning],
}

export function weatherDescription(code, isDay) {
  const [label, Icon] = WEATHER[code] || ['Conditions unavailable', Cloud]
  return [label, isDay === 0 && (code === 0 || code === 1) ? Moon : Icon]
}
