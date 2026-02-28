const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchApi<T = any>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function postApi<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

// Typed API calls
export const api = {
  getCityState: () => fetchApi('/api/traffic/city-state'),
  getHeatmap: () => fetchApi('/api/traffic/heatmap'),
  getIntersection: (id: string) => fetchApi(`/api/traffic/intersection/${id}`),
  getIntersections: () => fetchApi('/api/intersections/'),
  getLiveDecisions: () => fetchApi('/api/decisions/live'),
  getDecisionHistory: (page = 1) => fetchApi(`/api/decisions/history?page=${page}`),
  approveDecision: (id: string) => postApi(`/api/decisions/${id}/approve`),
  rejectDecision: (id: string) => postApi(`/api/decisions/${id}/reject`),
  getActiveEvents: () => fetchApi('/api/events/active'),
  getWeather: () => fetchApi('/api/weather/current'),
  getEmissions: () => fetchApi('/api/emissions/live'),
  getEmissionReport: () => fetchApi('/api/emissions/report'),
  getActiveAlerts: () => fetchApi('/api/alerts/active'),
  acknowledgeAlert: (id: string) => postApi(`/api/alerts/${id}/acknowledge`),
  getDatasourceStatus: () => fetchApi('/api/datasources/status'),
  getPredictions: (id: string) => fetchApi(`/api/predictions/${id}`),
  getActiveIncidents: () => fetchApi('/api/incidents/active'),
};
