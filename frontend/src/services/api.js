import { acquireAuthToken } from './msalInstance.js'

function methodNeedsAuth(method = 'GET') {
  const normalized = String(method).toUpperCase()
  return !['GET', 'HEAD', 'OPTIONS'].includes(normalized)
}

async function resolveAuthToken(method) {
  let token = await acquireAuthToken()
  if (!token && methodNeedsAuth(method)) {
    token = await acquireAuthToken({ interactive: true })
  }
  if (!token && methodNeedsAuth(method)) {
    throw new Error('401 Missing or invalid authentication. Please sign in again.')
  }
  return token
}

export async function apiFetch(url, opts = {}) {
  const method = opts.method || 'GET'
  const token = await resolveAuthToken(method)
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const r = await fetch(url, { ...opts, headers })
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
