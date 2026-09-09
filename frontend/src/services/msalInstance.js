import { PublicClientApplication } from "@azure/msal-browser";

function tenantId() {
  return (import.meta.env.VITE_AZURE_TENANT_ID || "").trim();
}

function clientId() {
  return (import.meta.env.VITE_AZURE_CLIENT_ID || "").trim();
}

/** Must match a redirect URI registered on the Azure AD app (include SPA base path if any). */
export function getMsalRedirectUri() {
  if (typeof window === "undefined") return "";
  const base = import.meta.env.BASE_URL || "/";
  const path = base.startsWith("/") ? base : `/${base}`;
  const withSlash = path.endsWith("/") ? path : `${path}/`;
  console.log("MSAL redirect URI:", `${window.location.origin}${withSlash}`);
  return `${window.location.origin}${withSlash}`;
}

let _instance;
let _instanceConfigKey = "";

/** Singleton MSAL client (lazy). Recreated when tenant/client env changes. */
export function getMsalInstance() {
  const tid = tenantId();
  const cid = clientId();
  const configKey = `${tid}|${cid}`;
  if (_instance && _instanceConfigKey === configKey) return _instance;
  if (!tid || !cid) {
    throw new Error(
      "Missing Azure AD config: set VITE_AZURE_TENANT_ID and VITE_AZURE_CLIENT_ID in frontend/.env",
    );
  }
  _instanceConfigKey = configKey;
  _instance = new PublicClientApplication({
    auth: {
      clientId: cid,
      authority: `https://login.microsoftonline.com/${tid}`,
      redirectUri: getMsalRedirectUri(),
    },
    cache: { cacheLocation: "sessionStorage", storeAuthStateInCookie: false },
  });
  return _instance;
}

export const loginRequest = {
  scopes: ["openid", "profile", "email"],
};

/** Restore MSAL active account from cache (needed after page reload). */
export async function ensureMsalAccount() {
  const msal = getMsalInstance();
  await msal.initialize();
  const active = msal.getActiveAccount();
  if (active) return active;
  const accounts = msal.getAllAccounts();
  if (!accounts.length) return null;
  msal.setActiveAccount(accounts[0]);
  return accounts[0];
}

/** Acquire a fresh Azure AD ID token for backend Bearer auth. Returns null when unauthenticated. */
export async function acquireAuthToken(options = {}) {
  const { interactive = false } = options;
  try {
    const account = await ensureMsalAccount();
    if (!account) return null;
    const msal = getMsalInstance();
    try {
      const result = await msal.acquireTokenSilent({
        ...loginRequest,
        account,
      });
      return result.idToken || null;
    } catch (silentError) {
      if (!interactive) throw silentError;
      const result = await msal.acquireTokenPopup({
        ...loginRequest,
        account,
        redirectUri: getMsalRedirectUri(),
      });
      if (result.account) {
        msal.setActiveAccount(result.account);
      }
      return result.idToken || null;
    }
  } catch {
    return null;
  }
}
