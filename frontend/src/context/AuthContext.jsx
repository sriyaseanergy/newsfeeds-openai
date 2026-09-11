import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { readStoredEmployee, clearStoredEmployee, persistEmployee } from "../services/auth.js";
import {
  clearLocalMsalSession,
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
    persistEmployee(sessionEmployee);
    ensureMsalAccount().catch(() => {});
  }, [sessionEmployee]);

  const logout = useCallback(async () => {
    clearStoredEmployee();
    setSessionEmployee(null);
    await clearLocalMsalSession();
  }, []);

  return (
    <AuthContext.Provider
      value={{ sessionEmployee, setSessionEmployee, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
