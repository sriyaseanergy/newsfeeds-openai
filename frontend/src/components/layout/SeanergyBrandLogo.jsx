import Box from '@mui/material/Box'
import seanergyAiLogo from '../../assets/images/Seanergy-AI-Logo.png'
import seanergySmallLogo from '../../assets/images/Seanergy-AI-Small-Logo.png'

export default function SeanergyBrandLogo({ collapsed, darkMode, height = 36 }) {
  if (collapsed) {
    return (
      <Box
        sx={{
          height: 32,
          width: 32,
          borderRadius: '22%',
          overflow: 'hidden',
          flexShrink: 0,
        }}
      >
        <Box
          component="img"
          src={seanergySmallLogo}
          alt="seanergy.ai"
          sx={{
            height: 32,
            width: 32,
            display: 'block',
            objectFit: 'cover',
            filter: darkMode ? 'none' : 'invert(1)',
          }}
        />
      </Box>
    )
  }

  return (
    <Box
      component="img"
      src={seanergyAiLogo}
      alt="seanergy.ai"
      sx={{
        height,
        width: 'auto',
        maxWidth: '100%',
        px: 2,
        display: 'block',
        objectFit: 'contain',
        filter: darkMode ? 'none' : 'invert(1)',
      }}
    />
  )
}
