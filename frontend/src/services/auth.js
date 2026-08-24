export const SESSION_KEY = "feed_alerts_engine_employee_session";

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

export function persistEmployee(employee) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ employee }));
}

export function clearStoredEmployee() {
  sessionStorage.removeItem(SESSION_KEY);
}

export function canManageFeedSources(employee) {
  return employee?.is_admin === true || employee?.can_manage_feed_sources === true
}
