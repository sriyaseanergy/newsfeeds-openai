import { useCallback, useMemo, useState } from 'react'
import { getMsalInstance, getMsalRedirectUri, loginRequest } from './msalInstance'

const SESSION_KEY = 'feed_alerts_engine_employee_session'

export function readStoredEmployee() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.employee ?? null
  } catch {
    return null
  }
}

export function persistEmployee(employee) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ employee }))
}

export function clearStoredEmployee() {
  sessionStorage.removeItem(SESSION_KEY)
}

const C = {
  pageBg: '#0e1015',
  panelBg: '#0a0b0e',
  border: 'rgba(255,255,255,0.07)',
  text: '#e2e4f0',
  muted: 'rgba(255,255,255,0.45)',
  accent: '#4f5fff',
  accentBg: 'rgba(79,95,255,0.15)',
  accentText: '#a0a8ff',
  red: '#f87171',
}

function apiBase() {
  const explicit = import.meta.env.VITE_API_BASE
  if (explicit) return String(explicit).replace(/\/+$/, '')
  const fromBackend = import.meta.env.VITE_API_BASE_PATH
  if (fromBackend) return String(fromBackend).replace(/\/+$/, '')
  return (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
}

export default function LoginPage({ onSignedIn }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const configured = useMemo(() => {
    const tid = String(
      import.meta.env.VITE_AZURE_TENANT_ID ||
        ''
    ).trim()
    const cid = String(
      import.meta.env.VITE_AZURE_CLIENT_ID ||
        ''
    ).trim()
    return !!(tid && cid)
  }, [])

  const signIn = useCallback(async () => {
    setError('')
    setBusy(true)
    try {
      const msal = getMsalInstance()
      await msal.initialize()
      msal.setActiveAccount(null)
      const res = await msal.loginPopup({
        ...loginRequest,
        redirectUri: getMsalRedirectUri(),
        prompt: 'select_account',
      })
      if (res.account) {
        msal.setActiveAccount(res.account)
      }
      const idToken = res.idToken
      if (!idToken) {
        setError('Sign-in did not return an ID token. Check the app registration (SPA) and scopes.')
        return
      }
      const url = `${apiBase()}/api/auth/session`
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: idToken }),
      })
      const data = await r.json().catch(() => ({}))
      if (!r.ok) {
        const msg =
          typeof data.detail === 'string'
            ? data.detail
            : data.detail?.[0]?.msg || `${r.status} ${r.statusText}`
        setError(msg || 'Sign-in failed')
        try {
          await msal.logoutPopup({ postLogoutRedirectUri: getMsalRedirectUri() })
        } catch {
          /* ignore */
        }
        return
      }
      if (!data.employee) {
        setError('Unexpected response from server')
        return
      }
      persistEmployee(data.employee)
      onSignedIn(data.employee)
    } catch (e) {
      setError(e?.message || String(e))
    } finally {
      setBusy(false)
    }
  }, [onSignedIn])

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: C.pageBg,
        color: C.text,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
        padding: 24,
      }}
    >
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.pageBg}; -webkit-font-smoothing: antialiased; }
      `}</style>
      <div
        style={{
          width: 'min(400px, 100%)',
          background: C.panelBg,
          border: `0.5px solid ${C.border}`,
          borderRadius: 12,
          padding: '28px 26px',
          boxShadow: '0 24px 80px rgba(0,0,0,0.35)',
        }}
      >
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', color: C.muted, textTransform: 'uppercase', marginBottom: 8 }}>
          Feed Alerts Engine
        </div>
        <h1 style={{ fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em', marginBottom: 8 }}>Sign in</h1>
        <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.5, marginBottom: 22 }}>
          Use your Microsoft work account. You must have an active employee record in MyWork.
        </p>

        {!configured && (
          <div
            style={{
              fontSize: 12,
              color: C.red,
              marginBottom: 14,
              padding: '10px 12px',
              borderRadius: 8,
              border: `0.5px solid rgba(248,113,113,0.35)`,
              background: 'rgba(248,113,113,0.06)',
            }}
          >
            Azure AD is not configured in the frontend build. Add{' '}
            <code style={{ fontSize: 11 }}>VITE_AZURE_TENANT_ID</code> and{' '}
            <code style={{ fontSize: 11 }}>VITE_AZURE_CLIENT_ID</code> to your <code style={{ fontSize: 11 }}>frontend/.env</code> and restart Vite.
          </div>
        )}

        <button
          type="button"
          disabled={busy || !configured}
          onClick={signIn}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            padding: '12px 16px',
            borderRadius: 8,
            border: `0.5px solid ${C.accent}`,
            background: C.accentBg,
            color: C.accentText,
            fontSize: 14,
            fontWeight: 600,
            cursor: busy || !configured ? 'not-allowed' : 'pointer',
            opacity: busy || !configured ? 0.55 : 1,
            fontFamily: 'inherit',
          }}
        >
          {busy ? 'Signing in…' : 'Sign in with Microsoft'}
        </button>

        {error && (
          <div style={{ marginTop: 14, fontSize: 12, color: C.red, lineHeight: 1.45 }}>{error}</div>
        )}

      </div>
    </div>
  )
}
