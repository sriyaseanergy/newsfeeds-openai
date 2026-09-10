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
  return `${window.location.origin}${withSlash}`;
}

export function isMsalConfigured() {
  return !!(tenantId() && clientId());
}

let _instance;
let _instanceConfigKey = "";
let _initializePromise = null;

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
  _initializePromise = null;
  _instance = new PublicClientApplication({
    auth: {
      clientId: cid,
      authority: `https://login.microsoftonline.com/${tid}`,
      redirectUri: getMsalRedirectUri(),
      navigateToLoginRequestUrl: false,
    },
    cache: { cacheLocation: "sessionStorage" },
  });
  return _instance;
}

export const loginRequest = {
  scopes: ["openid", "profile", "email"],
};

function isHashEmptyError(error) {
  const code = String(error?.errorCode || "").toLowerCase();
  const message = String(
    error?.message || error?.errorMessage || "",
  ).toLowerCase();
  return (
    code === "hash_empty_error" ||
    message.includes("hash value cannot be processed") ||
    message.includes("redirecturi is not clearing the hash")
  );
}

/** Drop stale redirect interaction keys when the URL hash was already cleared. */
function clearStaleRedirectInteractionState() {
  const cid = clientId();
  if (!cid || typeof window === "undefined") return;
  const prefix = `msal.${cid.toLowerCase()}`;
  try {
    for (let i = sessionStorage.length - 1; i >= 0; i -= 1) {
      const key = sessionStorage.key(i);
      if (!key) continue;
      const normalized = key.toLowerCase();
      if (
        normalized.startsWith(prefix) &&
        normalized.includes("interaction")
      ) {
        sessionStorage.removeItem(key);
      }
    }
  } catch {
    /* ignore storage errors */
  }
}

async function consumeRedirectResponse(msal) {
  try {
    const response = await msal.handleRedirectPromise();
    if (response?.account) {
      msal.setActiveAccount(response.account);
    }
    return response;
  } catch (error) {
    if (isHashEmptyError(error)) {
      clearStaleRedirectInteractionState();
      return null;
    }
    throw error;
  }
}

/**
 * Initialize MSAL once and consume any redirect hash before the router navigates.
 * Safe to call from login, logout, token refresh, and app bootstrap.
 */
export async function initializeMsal() {
  if (!isMsalConfigured()) return null;
  if (!_initializePromise) {
    _initializePromise = (async () => {
      const msal = getMsalInstance();
      await msal.initialize();
      await consumeRedirectResponse(msal);
      return msal;
    })().catch((error) => {
      _initializePromise = null;
      throw error;
    });
  }
  return _initializePromise;
}

/** Restore MSAL active account from cache (needed after page reload). */
export async function ensureMsalAccount() {
  const msal = await initializeMsal();
  if (!msal) return null;
  const active = msal.getActiveAccount();
  if (active) return active;
  const accounts = msal.getAllAccounts();
  if (!accounts.length) return null;
  msal.setActiveAccount(accounts[0]);
  return accounts[0];
}

/** Clear cached MSAL tokens locally without opening a Microsoft logout popup. */
export async function clearLocalMsalSession() {
  if (!isMsalConfigured()) return;
  try {
    const msal = await initializeMsal();
    if (!msal) return;
    msal.setActiveAccount(null);
    await msal.clearCache();
    clearStaleRedirectInteractionState();
  } catch {
    /* ignore */
  }
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
