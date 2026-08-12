import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const strip = (s = "") => s.trim().replace(/^\/+|\/+$/g, "");

/**
 * Load only frontend/.env.*. Browser-exposed values must use the VITE_ prefix.
 * Using prefix="" keeps all frontend env keys available to this config script.
 */
function loadFrontendEnv(mode) {
  return loadEnv(mode, __dirname, "");
}

export default defineConfig(({ mode }) => {
  const env = loadFrontendEnv(mode);

  // ── SPA base path ──────────────────────────────────────────────────────────
  // VITE_FRONTEND_URL=/feed-alerts/  →  base = "/feed-alerts/"
  // Unset                       →  base = "/"
  const frontendSegment = strip(
    env.VITE_FRONTEND_URL || ""
  );
  const base = frontendSegment ? `/${frontendSegment}/` : "/";

  // ── Backend API prefix ─────────────────────────────────────────────────────
  // VITE_ROOT_PATH=/feed-alerts-api  →  apiPrefix = "feed-alerts-api"
  const apiPrefix = strip(
    env.VITE_ROOT_PATH || ""
  );

  // ── What the frontend JS uses as the API base ──────────────────────────────
  // Dev:   always use the relative path (e.g. /feed-alerts-api) so the Vite
  //        proxy can intercept it and forward to the local backend.
  //        Using an absolute URL here would bypass the proxy entirely.
  // Build: prefer VITE_API_BASE (absolute URL) if set, so the built assets work
  //        regardless of whether API and SPA share the same origin.
  //        Falls back to the relative path for same-origin deployments.
  const relativeApiBase = apiPrefix ? `/${apiPrefix}` : "";
  const apiBase = mode === "development"
    ? (env.VITE_API_BASE || relativeApiBase)
    : (env.VITE_API_BASE || relativeApiBase);

  // ── Local dev backend target ───────────────────────────────────────────────
  // VITE_BACKEND_URL lets you point at a remote dev/staging backend.
  const backendTarget =
    env.VITE_BACKEND_URL ||
    "http://127.0.0.1:8000";

  // ── Dev proxy ─────────────────────────────────────────────────────────────
  // Rules:
  //   - Only the BACKEND prefix (/feed-alerts-api) is proxied — the frontend
  //     prefix (/feed-alerts) is served by the Vite dev server itself, never
  //     forwarded to the backend.
  //   - When no prefix is configured, fall back to proxying the individual
  //     API path segments directly.
  const proxy = {};

  if (apiPrefix) {
    // Strip the backend prefix before forwarding.
    // /feed-alerts-api/api/articles → /api/articles → http://127.0.0.1:8000
    proxy[`/${apiPrefix}`] = {
      target:       backendTarget,
      changeOrigin: true,
      rewrite: (p) => p.replace(new RegExp(`^/${apiPrefix}`), "") || "/",
    };
  } else {
    // No prefix — proxy individual API-shaped paths directly, stripping /api prefix when forwarding.
    for (const p of ["/api", "/authorize", "/callback", "/health"]) {
      proxy[p] = {
        target:       backendTarget,
        changeOrigin: true,
        rewrite: (path) => p === "/api" ? path.replace(/^\/api/, "") : path,
      };
    }
  }

  // ── Subpath redirect plugin ────────────────────────────────────────────────
  // Opening http://localhost:5173/ or http://localhost:5173/feed-alerts (no
  // trailing slash) when base="/feed-alerts/" causes assets to resolve from
  // the wrong path → blank page. Redirect to the canonical base URL instead.
  const spaRedirectPlugin = frontendSegment && {
    name: "spa-subpath-redirect",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const urlPath = (req.url || "").split("?")[0];
        if (urlPath === "/" || urlPath === `/${frontendSegment}`) {
          res.writeHead(302, { Location: `/${frontendSegment}/` });
          res.end();
          return;
        }
        next();
      });
    },
  };

  // ── Debug output ───────────────────────────────────────────────────────────
  console.log("[vite] base         =", base);
  console.log("[vite] apiBase      =", apiBase);
  console.log("[vite] apiPrefix    =", apiPrefix ? `/${apiPrefix}` : "(none)");
  console.log("[vite] backendTarget=", backendTarget);
  console.log("[vite] proxy keys   =", Object.keys(proxy));

  return {
    envDir: __dirname,

    plugins: [react(), spaRedirectPlugin].filter(Boolean),

    base,

    define: {
      // Expose the resolved API base to frontend JS.
      // App.jsx reads import.meta.env.VITE_API_BASE first, then VITE_API_BASE_PATH.
      "import.meta.env.VITE_API_BASE":      JSON.stringify(apiBase),
      // Keep VITE_API_BASE_PATH for any code still referencing the old name.
      "import.meta.env.VITE_API_BASE_PATH": JSON.stringify(apiBase),
    },

    server: {
      port: 5173,
      proxy,
    },

    build: {
      outDir:     "dist",
      emptyOutDir: true,
    },
  };
});
