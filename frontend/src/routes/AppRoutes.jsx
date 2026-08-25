import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import AppLayout from "../components/layout/AppLayout.jsx";
import LoginPage from "../pages/publicPages/LoginPage.jsx";
import ArticlesPage from "../pages/protectedPages/ArticlesPage.jsx";
import FeedHealthPage from "../pages/protectedPages/FeedHealthPage.jsx";
import SettingsPage from "../pages/protectedPages/SettingsPage.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";
import Paper from "@mui/material/Paper";
import { useAppData } from "../context/AppDataContext.jsx";

function FeedHealthRoute() {
  const { feedHealth, healthLoading, fetchFeedHealth } = useAppData();
  return (
    <Paper
      elevation={0}
      sx={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        borderRadius: 2,
        border: 1,
        borderColor: "divider",
      }}
    >
      <FeedHealthPage
        feedHealth={feedHealth}
        loading={healthLoading}
        onRefresh={fetchFeedHealth}
      />
    </Paper>
  );
}

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
          <Route path="feed-health" element={<FeedHealthRoute />} />
          <Route path="settings" element={<SettingsRoute />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/articles" replace />} />
    </Routes>
  );
}
