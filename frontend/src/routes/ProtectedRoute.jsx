import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { AppDataProvider } from '../context/AppDataContext.jsx'

export default function ProtectedRoute() {
  const { sessionEmployee } = useAuth()

  if (!sessionEmployee) {
    return <Navigate to="/login" replace />
  }

  return (
    <AppDataProvider>
      <Outlet />
    </AppDataProvider>
  )
}
