import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { readStoredEmployee, clearStoredEmployee } from "../services/auth.js";
import {
  getMsalInstance,
  getMsalRedirectUri,
  ensureMsalAccount,
} from "../services/msalInstance.js";

const AuthContext = createContext(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }) {
  const [sessionEmployee, setSessionEmployee] = useState(() =>
    readStoredEmployee(),
  );

  useEffect(() => {
    if (!sessionEmployee) return;
    ensureMsalAccount().catch(() => {});
  }, [sessionEmployee]);

  const logout = useCallback(async () => {
    clearStoredEmployee();
    setSessionEmployee(null);
    try {
      const msal = getMsalInstance();
      await msal.initialize();
      await msal.logoutPopup({ postLogoutRedirectUri: getMsalRedirectUri() });
    } catch {
      /* ignore */
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ sessionEmployee, setSessionEmployee, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
