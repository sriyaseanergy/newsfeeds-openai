import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import SeaSignalLogo from "../../components/SeaSignalLogo.jsx";
import { useNotification } from "../../components/notificationController.tsx";
import seasignalBg from "../../assets/images/seasignal-bg.png";
import { API } from "../../config/api.js";
import { persistEmployee } from "../../services/auth.js";
import {
  getMsalInstance,
  getMsalRedirectUri,
  loginRequest,
} from "../../services/msalInstance.js";
import { useAuth } from "../../context/AuthContext.jsx";

function MicrosoftLogo() {
  return (
    <svg
      width="21"
      height="21"
      viewBox="0 0 21 21"
      aria-hidden="true"
      style={{ flexShrink: 0 }}
    >
      <rect x="1" y="1" width="9" height="9" fill="#f25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
      <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
      <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
    </svg>
  );
}

function isUserCancellationError(error) {
  const code = String(error?.errorCode || "").toLowerCase();
  const message = String(
    error?.message || error?.errorMessage || error || "",
  ).toLowerCase();
  return (
    code === "user_cancelled" ||
    message.includes("user_cancelled") ||
    message.includes("user cancelled")
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { setSessionEmployee } = useAuth();
  const { showNotification } = useNotification();
  const [busy, setBusy] = useState(false);
  const configWarningShown = useRef(false);

  const configured = useMemo(() => {
    const tid = String(import.meta.env.VITE_AZURE_TENANT_ID || "").trim();
    const cid = String(import.meta.env.VITE_AZURE_CLIENT_ID || "").trim();
    return !!(tid && cid);
  }, []);

  useEffect(() => {
    if (!configured && !configWarningShown.current) {
      configWarningShown.current = true;
      showNotification({
        severity: "warning",
        status: "Warning",
        description:
          "Azure AD is not configured. Add VITE_AZURE_TENANT_ID and VITE_AZURE_CLIENT_ID to frontend/.env and restart Vite.",
        autoHideMs: 0,
      });
    }
  }, [configured, showNotification]);

  const signIn = useCallback(async () => {
    setBusy(true);
    try {
      const msal = getMsalInstance();
      await msal.initialize();
      msal.setActiveAccount(null);
      const res = await msal.loginPopup({
        ...loginRequest,
        redirectUri: getMsalRedirectUri(),
        prompt: "select_account",
      });
      if (res.account) {
        msal.setActiveAccount(res.account);
      }
      const idToken = res.idToken;
      if (!idToken) {
        showNotification({
          severity: "error",
          description:
            "Sign-in did not return an ID token. Check the app registration (SPA) and scopes.",
        });
        return;
      }
      const r = await fetch(API.authSession, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken }),
      });
      const raw = await r.text();
      let data = {};
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        if (!r.ok) {
          showNotification({
            severity: "error",
            message: raw || `${r.status} ${r.statusText}`,
          });
          return;
        }
      }
      if (!r.ok) {
        const msg =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.[0]?.msg || raw || r.statusText;
        showNotification({
          severity: "error",
          status: String(r.status),
          description: msg || "Sign-in failed",
        });
        return;
      }
      if (!data.employee) {
        showNotification({
          severity: "error",
          description: "Unexpected response from server",
        });
        return;
      }
      persistEmployee(data.employee);
      setSessionEmployee(data.employee);
      navigate("/articles", { replace: true });
    } catch (e) {
      if (!isUserCancellationError(e)) {
        showNotification({
          severity: "error",
          message: e?.message || String(e),
        });
      }
    } finally {
      setBusy(false);
    }
  }, [navigate, setSessionEmployee, showNotification]);

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        backgroundImage: `url(${seasignalBg})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundAttachment: "fixed",
      }}
    >
      <Card
        elevation={0}
        sx={{
          width: 425,
          maxWidth: "calc(100vw - 32px)",
          p: "42px 42px 28px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          borderRadius: 3,
          bgcolor: "rgba(8, 20, 48, 0.72)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border: "1px solid rgba(100, 180, 255, 0.22)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.35)",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 1.25,
            width: "100%",
          }}
        >
          <SeaSignalLogo forceDarkBg />
          <Typography
            component="div"
            sx={{
              height: 56,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
              fontSize: 28,
              fontWeight: 500,
              letterSpacing: "2px",
              color: "#ffffff",
              lineHeight: 1.2,
              textAlign: "center",
            }}
          >
            Sea Signal
          </Typography>
        </Box>

        <Box
          sx={{
            width: "100%",
            mt: 5,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Typography
            variant="body1"
            textAlign="center"
            sx={{
              mb: 3.5,
              color: "rgba(200, 220, 240, 0.85)",
              fontWeight: 500,
              fontSize: 18,
              lineHeight: 1.5,
            }}
          >
            Use your Microsoft Account to Sign In.
          </Typography>

          <Button
            fullWidth
            variant="outlined"
            size="large"
            disabled={busy || !configured}
            onClick={signIn}
            startIcon={<MicrosoftLogo />}
            sx={{
              height: 56,
              fontSize: 18,
              fontWeight: 400,
              color: "#ffffff",
              borderColor: "rgba(100, 180, 255, 0.35)",
              bgcolor: "rgba(255, 255, 255, 0.06)",
              "&:hover": {
                color: "#29c5f4",
                borderColor: "#29c5f4",
                bgcolor: "rgba(41, 197, 244, 0.08)",
              },
              "&.Mui-disabled": {
                color: "rgba(255,255,255,0.35)",
                borderColor: "rgba(255,255,255,0.15)",
              },
            }}
          >
            Sign in with Microsoft
          </Button>
        </Box>

        <Typography
          variant="caption"
          sx={{
            mt: 2.5,
            textAlign: "center",
            width: "100%",
            color: "rgba(180, 200, 220, 0.75)",
            fontWeight: 500,
            fontSize: 14,
            lineHeight: 1.5,
          }}
        >
          © Seanergy.ai group. All rights reserved
        </Typography>
      </Card>
    </Box>
  );
}
