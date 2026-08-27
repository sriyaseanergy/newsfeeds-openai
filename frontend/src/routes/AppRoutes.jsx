import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import AppLayout from "../components/layout/AppLayout.jsx";
import LoginPage from "../pages/publicPages/LoginPage.jsx";
import ArticlesPage from "../pages/protectedPages/ArticlesPage.jsx";
import SettingsPage from "../pages/protectedPages/SettingsPage.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";

function SettingsRoute() {
  return <SettingsPage />;
}

function PublicLoginRoute() {
  const { sessionEmployee } = useAuth();
  if (sessionEmployee) {
    return <Navigate to="/articles" replace />;
  }
  return <LoginPage />;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PublicLoginRoute />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/articles" replace />} />
          <Route path="articles" element={<ArticlesPage />} />
          <Route path="settings" element={<SettingsRoute />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/articles" replace />} />
    </Routes>
  );
}
