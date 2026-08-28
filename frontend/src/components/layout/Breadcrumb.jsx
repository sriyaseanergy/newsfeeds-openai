import { Link as RouterLink, useLocation } from "react-router-dom";
import Box from "@mui/material/Box";
import Breadcrumbs from "@mui/material/Breadcrumbs";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { FONT_FAMILY } from "../../config/theme.js";
import { IconHome } from "./LayoutIcons.jsx";

export default function Breadcrumb({ selectedCat }) {
  const location = useLocation();
  const path = location.pathname;

  const pageLabel = path.includes("/settings")
      ? "Settings"
      : selectedCat || "Articles";

  return (
    <Box
      sx={{
        px: 3,
        py: 2,
        flexShrink: 0,
        borderBottom: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
      }}
    >
      <Breadcrumbs
        separator="/"
        sx={{
          fontFamily: FONT_FAMILY,
          fontSize: 16,
          lineHeight: 1,
          "& .MuiBreadcrumbs-ol": {
            alignItems: "center",
            flexWrap: "nowrap",
          },
          "& .MuiBreadcrumbs-li": {
            display: "flex",
            alignItems: "center",
          },
          "& .MuiBreadcrumbs-separator": {
            mx: 0.75,
            display: "flex",
            alignItems: "center",
            fontSize: 16,
            lineHeight: 1,
          },
        }}
      >
        <Link
          component={RouterLink}
          to="/articles"
          underline="hover"
          color="inherit"
          aria-label="Home"
          sx={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            lineHeight: 1,
            "& .MuiSvgIcon-root": {
              fontSize: 17,
              width: 17,
              height: 17,
              transform: "translateY(1px)",
            },
          }}
        >
          <IconHome size={18} />
        </Link>
        <Typography
          component="span"
          color="text.primary"
          sx={{
            display: "inline-flex",
            alignItems: "center",
            fontFamily: FONT_FAMILY,
            fontSize: 16,
            fontWeight: 500,
            lineHeight: 1,
          }}
        >
          {pageLabel}
        </Typography>
      </Breadcrumbs>
    </Box>
  );
}
