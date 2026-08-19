import { acquireAuthToken } from './msalInstance.js'

export async function apiFetch(url, opts = {}) {
  const token = await acquireAuthToken()
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const r = await fetch(url, { headers, ...opts })
  if (!r.ok) {
    let detail = ''
    try {
      const body = await r.json()
      if (typeof body?.detail === 'string') detail = body.detail
      else if (Array.isArray(body?.detail) && body.detail.length) {
        detail = body.detail.map(d => d?.msg || d?.message).filter(Boolean).join(', ')
      } else if (typeof body?.message === 'string') {
        detail = body.message
      }
    } catch {
      try {
        detail = await r.text()
      } catch {
        detail = ''
      }
    }
    throw new Error(`${r.status} ${detail || r.statusText}`)
  }
  if (r.status === 204) return null
  return r.json()
}
