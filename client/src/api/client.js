import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 18000 })

export const getCurrentWeather = (location, source, signal) =>
  api.get(`/weather/current/${encodeURIComponent(location)}`, { params: { source }, signal }).then(response => response.data)

export const getForecast = (location, source, signal) =>
  api.get(`/weather/forecast/${encodeURIComponent(location)}`, { params: { source }, signal }).then(response => response.data)

export const getForecastRisk = (location, source, activity, signal) =>
  api.get(`/predict/forecast/${encodeURIComponent(location)}`, { params: { source, activity }, signal }).then(response => response.data)

export const predictRisk = (selection, signal) =>
  api.post('/predict/risk', selection, { signal }).then(response => response.data)

export const getRecommendations = (selection, signal) =>
  api.post('/recommend/activity', selection, { signal }).then(response => response.data)

export const errorMessage = error => {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Check the activity, date and time, then try again.'
  return 'Could not reach the OutRisk service. Please try again.'
}
