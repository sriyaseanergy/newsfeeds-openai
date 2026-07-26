/** SVG icons for app layout shell. */

import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined'
import PersonIcon from '@mui/icons-material/Person'
import LogoutIcon from '@mui/icons-material/Logout'
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined'
import BuildOutlinedIcon from '@mui/icons-material/BuildOutlined'
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined'
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined'
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import MonitorHeartOutlinedIcon from '@mui/icons-material/MonitorHeartOutlined'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'

const iconStyle = { width: 20, height: 20, display: 'block' }
const menuIconProps = { fontSize: 'medium', sx: { display: 'block' } }

const profileIconProps = { sx: { display: 'block', fontSize: 20 } }

export function IconNotes({ size = 30, color }) {
  return (
    <svg
      style={{ width: size, height: size, display: 'block', color: color || 'currentColor' }}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M3 18h12v-2H3v2zM3 6v2h18V6H3zm0 7h18v-2H3v2z" />
    </svg>
  )
}

export function IconMenu({ size = 20 }) {
  return (
    <svg style={{ width: size, height: size, display: 'block' }} viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
    </svg>
  )
}

export function IconChevronRight({ size = 20 }) {
  return (
    <svg style={{ width: size, height: size, display: 'block' }} viewBox="0 0 24 24" fill="currentColor">
      <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
    </svg>
  )
}

export function IconChevronLeft() {
  return (
    <svg style={iconStyle} viewBox="0 0 24 24" fill="currentColor">
      <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
    </svg>
  )
}

export function IconSearch() {
  return (
    <svg style={{ width: 18, height: 18, display: 'block' }} viewBox="0 0 24 24" fill="currentColor">
      <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
    </svg>
  )
}

const headerIconStyle = { width: 22, height: 22, display: 'block' }

export function IconTranslate() {
  return (
    <svg style={headerIconStyle} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12.87 15.07l-2.54-2.51.03-.03c1.74-1.94 2.98-4.17 3.71-6.53H17V4h-7V2H8v2H1v1.99h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04zM18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z" />
    </svg>
  )
}

export function IconDarkMode() {
  return (
    <svg style={headerIconStyle} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 3a9 9 0 109 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 01-4.4 2.26 5.403 5.403 0 01-3.14-9.8c-.44-.06-.9-.1-1.36-.1z" />
    </svg>
  )
}

export function IconLightMode() {
  return (
    <svg style={headerIconStyle} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a1 1 0 00-1.41 0 1 1 0 000 1.41l1.06 1.06a1 1 0 001.41-1.41L5.99 4.58zm12.37 12.37a1 1 0 00-1.41 0 1 1 0 000 1.41l1.06 1.06a1 1 0 001.41-1.41l-1.06-1.06zm1.06-10.96a1 1 0 000-1.41 1 1 0 00-1.41 0l-1.06 1.06a1 1 0 101.41 1.41l1.06-1.06zM7.05 18.36a1 1 0 00-1.41 0 1 1 0 000 1.41l1.06 1.06a1 1 0 001.41-1.41l-1.06-1.06z" />
    </svg>
  )
}

export function IconNotifications() {
  return (
    <svg style={headerIconStyle} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
    </svg>
  )
}

export function IconDashboard() {
  return (
    <svg style={iconStyle} viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
    </svg>
  )
}

export function IconHome() {
  return (
    <HomeOutlinedIcon
      sx={{
        display: 'block',
        fontSize: 13,
        width: 13,
        height: 13,
      }}
    />
  )
}

export function IconSecurity() {
  return <SecurityOutlinedIcon {...menuIconProps} />
}

export function IconEngineering() {
  return <BuildOutlinedIcon {...menuIconProps} />
}

export function IconPsychology() {
  return <PsychologyOutlinedIcon {...menuIconProps} />
}

export function IconLightbulb() {
  return <LightbulbOutlinedIcon {...menuIconProps} />
}

export function IconArticle() {
  return <DescriptionOutlinedIcon {...menuIconProps} />
}

export function IconFeedHealth() {
  return <MonitorHeartOutlinedIcon {...menuIconProps} />
}

export function IconSettings() {
  return <SettingsOutlinedIcon {...menuIconProps} />
}

export function IconPerson() {
  return <PersonIcon {...profileIconProps} />
}

export function IconLogout() {
  return <LogoutIcon {...profileIconProps} />
}