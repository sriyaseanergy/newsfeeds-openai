export const SESSION_KEY = "feed_alerts_engine_employee_session";
export const IS_ADMIN_KEY = "feed_alerts_is_admin";

export function readStoredEmployee() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.employee ?? null;
  } catch {
    return null;
  }
}

export function readIsAdmin() {
  return localStorage.getItem(IS_ADMIN_KEY) === "true";
}

export function persistEmployee(employee) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ employee }));
  localStorage.setItem(
    IS_ADMIN_KEY,
    employee?.is_admin === true ? "true" : "false",
  );
}

export function clearStoredEmployee() {
  sessionStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(IS_ADMIN_KEY);
}

export function isAdmin(employee) {
  return employee?.is_admin === true || readIsAdmin();
}

export function canManageFeedSources(employee) {
  return isAdmin(employee);
}
