import Box from '@mui/material/Box'
import seasignalLogoDark from '../assets/images/seasignal-logo-dark.png'
import seasignalLogoLight from '../assets/images/seasignal-logo-light.png'
import { useThemeMode } from '../context/ThemeProviderWrapper.jsx'

const LOGO_SIZE = 56

const logoImageSx = {
  position: 'absolute',
  inset: 0,
  height: LOGO_SIZE,
  width: LOGO_SIZE,
  objectFit: 'contain',
  display: 'block',
}

/** Preload both theme variants so login/logout never waits on image fetch. */
export function preloadSeaSignalLogos() {
  for (const src of [seasignalLogoDark, seasignalLogoLight]) {
    const img = new Image()
    img.src = src
  }
}

export default function SeaSignalLogo({ forceDarkBg = false }) {
  const { darkMode } = useThemeMode()
  const useLightLogo = forceDarkBg || darkMode

  return (
    <Box
      sx={{
        position: 'relative',
        width: LOGO_SIZE,
        height: LOGO_SIZE,
        flexShrink: 0,
      }}
      aria-hidden
    >
      <Box
        component="img"
        src={seasignalLogoLight}
        alt=""
        loading="eager"
        decoding="sync"
        sx={{
          ...logoImageSx,
          visibility: useLightLogo ? 'hidden' : 'visible',
        }}
      />
      <Box
        component="img"
        src={seasignalLogoDark}
        alt=""
        loading="eager"
        decoding="sync"
        sx={{
          ...logoImageSx,
          visibility: useLightLogo ? 'visible' : 'hidden',
        }}
      />
    </Box>
  )
}

export { LOGO_SIZE as SEA_SIGNAL_LOGO_SIZE }
