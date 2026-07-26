import { PublicClientApplication } from '@azure/msal-browser'

function tenantId() {
  return (
    import.meta.env.VITE_AZURE_TENANT_ID ||
    ''
  ).trim()
}

function clientId() {
  return (
    import.meta.env.VITE_AZURE_CLIENT_ID ||
    ''
  ).trim()
}

/** Must match a redirect URI registered on the Azure AD app (include SPA base path if any). */
export function getMsalRedirectUri() {
  if (typeof window === 'undefined') return ''
  const base = import.meta.env.BASE_URL || '/'
  const path = base.startsWith('/') ? base : `/${base}`
  const withSlash = path.endsWith('/') ? path : `${path}/`
  return `${window.location.origin}${withSlash}`
}

let _instance

/** Singleton MSAL client (lazy). */
export function getMsalInstance() {
  if (_instance) return _instance
  const tid = tenantId()
  const cid = clientId()
  if (!tid || !cid) {
    throw new Error(
      'Missing Azure AD config: set VITE_AZURE_TENANT_ID and VITE_AZURE_CLIENT_ID in frontend/.env'
    )
  }
  _instance = new PublicClientApplication({
    auth: {
      clientId: cid,
      authority: `https://login.microsoftonline.com/${tid}`,
      redirectUri: getMsalRedirectUri(),
    },
    cache: { cacheLocation: 'sessionStorage' },
  })
  return _instance
}

export const loginRequest = {
  scopes: ['openid', 'profile', 'email'],
}
