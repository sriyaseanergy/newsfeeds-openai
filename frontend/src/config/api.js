export const API_BASE = (() => {
  const explicit = import.meta.env.VITE_API_BASE
  if (explicit) return String(explicit).replace(/\/+$/, '')
  const fromBackend = import.meta.env.VITE_API_BASE_PATH
  if (fromBackend) return String(fromBackend).replace(/\/+$/, '')
  return (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
})()

export const API = {
  articles: `${API_BASE}/api/articles`,
  emails: `${API_BASE}/api/email-recipients`,
  feeds: `${API_BASE}/api/feeds`,
  technologyDomains: `${API_BASE}/api/technology-domains`,
  status: `${API_BASE}/api/status`,
  feedsHealth: `${API_BASE}/api/feeds/health`,
  authSession: `${API_BASE}/api/auth/session`,
}

export const routerBasename = (() => {
  const base = import.meta.env.BASE_URL || '/'
  const trimmed = base.replace(/\/+$/, '')
  return trimmed || undefined
})()
