import Box from '@mui/material/Box'
import loaderGif from '../assets/images/Loader.gif'

export default function CustomLoader() {
  return (
    <Box className="custom-loader-overlay">
      <Box
        component="img"
        src={loaderGif}
        alt="Loading"
        className="custom-loader-image"
      />
    </Box>
  )
}
