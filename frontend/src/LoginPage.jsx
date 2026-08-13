import { useCallback, useMemo, useState } from 'react'
import seanergyIcon from './assets/seanergy-icon.png'
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
  pageBg: '#f5f6f6',
  cardBg: '#ffffff',
  border: '#dedede',
  text: '#1a1a1a',
  muted: '#6b7280',
  subtitle: '#9ca3af',
  accentGreen: '#318524',
  buttonBorder: '#d9d9d9',
  red: '#dc2626',
  redBg: '#fef2f2',
  redBorder: '#fecaca',
  warnBg: '#fffbeb',
  warnBorder: '#fde68a',
  warnText: '#92400e',
}

function apiBase() {
  const explicit = import.meta.env.VITE_API_BASE
  if (explicit) return String(explicit).replace(/\/+$/, '')
  const fromBackend = import.meta.env.VITE_API_BASE_PATH
  if (fromBackend) return String(fromBackend).replace(/\/+$/, '')
  return (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
}

function MicrosoftLogo() {
  return (
    <svg width="21" height="21" viewBox="0 0 21 21" aria-hidden="true" style={{ flexShrink: 0 }}>
      <rect x="1" y="1" width="9" height="9" fill="#f25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
      <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
      <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
    </svg>
  )
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
        padding: 16,
      }}
    >
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.pageBg}; -webkit-font-smoothing: antialiased; }
      `}</style>
      <div
        style={{
          width: 475,
          maxWidth: 'calc(100vw - 32px)',
          minHeight: 425,
          background: C.cardBg,
          border: `1px solid ${C.border}`,
          borderRadius: 16,
          padding: 42,
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <div style={{ textAlign: 'center', width: '100%' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <img
              src={seanergyIcon}
              alt=""
              width={22}
              height={22}
              style={{ display: 'block', objectFit: 'contain' }}
            />
            <span
              style={{
                fontSize: 24,
                fontWeight: 600,
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
              }}
            >
              <span style={{ color: C.text }}>seanergy</span>
              <span style={{ color: C.accentGreen }}>.ai</span>
            </span>
          </div>
          <div
            style={{
              marginTop: 6,
              fontSize: 13,
              fontWeight: 500,
              letterSpacing: '2px',
              color: C.subtitle,
            }}
          >
            SeaSignal
          </div>
        </div>

        <div
          style={{
            width: '100%',
            marginTop: 42,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            flex: 1,
          }}
        >
          <h1
            style={{
              fontSize: 26,
              fontWeight: 600,
              color: C.text,
              textAlign: 'center',
              marginBottom: 16,
              letterSpacing: '-0.01em',
            }}
          >
            Sign in
          </h1>
          <p
            style={{
              fontSize: 16,
              color: C.muted,
              lineHeight: 1.5,
              textAlign: 'center',
              maxWidth: 340,
              marginBottom: 28,
            }}
          >
            Use your Microsoft work account. You must have an active employee record in MyWork.
          </p>

          {!configured && (
            <div
              style={{
                width: '100%',
                fontSize: 13,
                color: C.warnText,
                marginBottom: 16,
                padding: '12px 14px',
                borderRadius: 10,
                border: `1px solid ${C.warnBorder}`,
                background: C.warnBg,
                lineHeight: 1.45,
                textAlign: 'center',
              }}
            >
              Azure AD is not configured in the frontend build. Add{' '}
              <code style={{ fontSize: 12 }}>VITE_AZURE_TENANT_ID</code> and{' '}
              <code style={{ fontSize: 12 }}>VITE_AZURE_CLIENT_ID</code> to your{' '}
              <code style={{ fontSize: 12 }}>frontend/.env</code> and restart Vite.
            </div>
          )}

          <button
            type="button"
            disabled={busy || !configured}
            onClick={signIn}
            style={{
              width: '100%',
              height: 56,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 12,
              borderRadius: 10,
              border: `1px solid ${C.buttonBorder}`,
              background: C.cardBg,
              color: C.text,
              fontSize: 16,
              fontWeight: 500,
              cursor: busy || !configured ? 'not-allowed' : 'pointer',
              opacity: busy || !configured ? 0.55 : 1,
              fontFamily: 'inherit',
              boxShadow: 'none',
            }}
          >
            <MicrosoftLogo />
            {busy ? 'Signing in...' : 'Sign in with Microsoft'}
          </button>

          {error && (
            <div
              style={{
                width: '100%',
                marginTop: 16,
                fontSize: 14,
                color: C.red,
                lineHeight: 1.45,
                textAlign: 'center',
                padding: '10px 12px',
                borderRadius: 8,
                border: `1px solid ${C.redBorder}`,
                background: C.redBg,
              }}
            >
              {error}
            </div>
          )}
        </div>

        <p
          style={{
            marginTop: 32,
            fontSize: 13,
            color: C.subtitle,
            textAlign: 'center',
            width: '100%',
          }}
        >
          © seanergy.ai group. All rights reserved
        </p>
      </div>
    </div>
  )
}
