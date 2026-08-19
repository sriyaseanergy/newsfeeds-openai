import { createTheme } from "@mui/material/styles";

export const BRAND = {
  main: "#318524",
  light: "#4a9e3a",
  dark: "#1e5a16",
  menuHover: "#E8F5E9",
  hoverBorder: "#318524",
  tableHeader: "#318524",
  editIcon: "#318524",
  editHover: "rgba(49, 133, 36, 0.06)",
  rowHover: "#edf7eb",
};

export const LAYOUT = {
  headerHeight: 64,
  drawerWidth: 240,
  drawerCollapsed: 64,
  footerHeight: 36,
  pageBg: "#fafafa",
  panelBg: "#ffffff",
  border: "#e0e0e0",
  text: "#000000",
  textSecondary: "#555555",
  textMuted: "#666666",
};

export const LAYOUT_DARK = {
  ...LAYOUT,
  pageBg: "#0f0f0f",
  panelBg: "#1a1a1a",
  border: "#2e2e2e",
  text: "#e8e8e8",
  textSecondary: "#a0a0a0",
  textMuted: "#888888",
};

export const THEME_STORAGE_KEY = "fa-theme";

export const FONT_FAMILY = '"Barlow Condensed", sans-serif';

export const CATEGORY_COLORS = {
  "Risks & Threats": "#f87171",
  Engineering: "#2563eb",
  "AI & Machine Learning": "#a78bfa",
  "Expert Context": "#fb923c",
  Security: "#f87171",
  AI: "#a78bfa",
  ML: "#818cf8",
  Frontend: "#60a5fa",
  Backend: "#2563eb",
  BI: "#fb923c",
  Dev: "#4f5fff",
};

export function catColor(cat) {
  return CATEGORY_COLORS[cat] || "rgba(15,23,42,0.4)";
}

const TYPOGRAPHY_VARIANTS = [
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "subtitle1",
  "subtitle2",
  "body1",
  "body2",
  "button",
  "caption",
  "overline",
];

const fontWeight500Variants = Object.fromEntries(
  TYPOGRAPHY_VARIANTS.map(key => [key, { fontWeight: 500 }]),
);

const typographyVariantOverrides = Object.fromEntries(
  TYPOGRAPHY_VARIANTS.map(key => [key, { fontWeight: 500 }]),
);

export function createAppTheme(mode = "light") {
  const isDark = mode === "dark";
  const layout = isDark ? LAYOUT_DARK : LAYOUT;

  return createTheme({
    palette: {
      mode,
      primary: {
        main: BRAND.main,
        light: BRAND.light,
        dark: BRAND.dark,
        contrastText: "#ffffff",
      },
      background: {
        default: layout.pageBg,
        paper: layout.panelBg,
      },
      text: {
        primary: layout.text,
        secondary: layout.textSecondary,
      },
      divider: layout.border,
      error: { main: "#f87171" },
      warning: { main: "#fbbf24" },
      success: { main: BRAND.main },
    },
    typography: {
      fontFamily: FONT_FAMILY,
      fontWeightLight: 500,
      fontWeightRegular: 500,
      fontWeightMedium: 500,
      fontWeightBold: 500,
      ...fontWeight500Variants,
      allVariants: {
        fontWeight: 500,
      },
    },
    shape: {
      borderRadius: 6,
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          html: {
            fontWeight: 500,
          },
          body: {
            fontFamily: FONT_FAMILY,
            fontWeight: 500,
            WebkitFontSmoothing: "antialiased",
          },
          "#root": {
            fontWeight: 500,
          },
          "input, textarea, select, button": {
            fontWeight: 500,
          },
        },
      },
      MuiTypography: {
        styleOverrides: {
          root: {
            fontFamily: FONT_FAMILY,
            fontWeight: 500,
          },
          ...typographyVariantOverrides,
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
            fontWeight: 500,
          },
        },
      },
    },
  });
}

export const themeTokens = { BRAND, LAYOUT, LAYOUT_DARK };
