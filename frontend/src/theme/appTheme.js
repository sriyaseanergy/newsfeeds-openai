/** Feed Alerts Engine — app layout design tokens. */

export const BRAND = {
  main: '#318524',
  light: '#4a9e3a',
  dark: '#1e5a16',
  menuHover: '#E8F5E9',
  hoverBorder: '#318524',
  tableHeader: '#318524',
  editIcon: '#318524',
  editHover: 'rgba(49, 133, 36, 0.06)',
  rowHover: '#edf7eb',
}

export const LAYOUT = {
  headerHeight: 64,
  drawerWidth: 240,
  drawerCollapsed: 64,
  footerHeight: 36,
  pageBg: '#fafafa',
  panelBg: '#ffffff',
  border: '#e0e0e0',
  text: '#000000',
  textSecondary: '#555555',
  textMuted: '#666666',
}

export const LAYOUT_DARK = {
  ...LAYOUT,
  pageBg: '#0f0f0f',
  panelBg: '#1a1a1a',
  border: '#2e2e2e',
  text: '#e8e8e8',
  textSecondary: '#a0a0a0',
  textMuted: '#888888',
}

export const THEME_STORAGE_KEY = 'fa-theme'

export const themeTokens = { BRAND, LAYOUT, LAYOUT_DARK }
