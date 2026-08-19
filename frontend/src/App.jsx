import { BrowserRouter } from 'react-router-dom'
import { ThemeProviderWrapper } from './context/ThemeProviderWrapper.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { routerBasename } from './config/api.js'
import AppRoutes from './routes/AppRoutes.jsx'

export default function App() {
    return (
    <ThemeProviderWrapper>
      <AuthProvider>
        <BrowserRouter basename={routerBasename}>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProviderWrapper>
    )
}
