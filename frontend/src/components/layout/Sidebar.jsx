import { NavLink, useLocation } from "react-router-dom";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Badge from "@mui/material/Badge";
import Box from "@mui/material/Box";
import Tooltip from "@mui/material/Tooltip";
import { useTheme } from "@mui/material/styles";
import { LAYOUT, BRAND, FONT_FAMILY } from "../../config/theme.js";
import { catCount, technologyDomainNames } from "../../utils/articles.js";
import {
  IconSettings,
  IconPsychology,
  IconLightbulb,
  IconArticle,
} from "./LayoutIcons.jsx";

const CATEGORY_SIDEBAR_ICONS = [IconArticle, IconLightbulb, IconPsychology];

function technologyDomainIcon(index) {
  return CATEGORY_SIDEBAR_ICONS[index % CATEGORY_SIDEBAR_ICONS.length];
}

function sidebarItemBaseSx(theme, collapsed) {
  const isDark = theme.palette.mode === "dark";
  return {
    borderRadius: 1.5,
    mx: 1,
    mb: 0.5,
    minHeight: 40,
    justifyContent: collapsed ? "center" : "flex-start",
    px: collapsed ? 1 : 2,
    ...(isDark && {
      color: "#ffffff",
      "& .MuiListItemIcon-root": { color: "#ffffff" },
      "& .MuiListItemText-primary": { color: "#ffffff" },
    }),
  };
}

function activeItemSx() {
  return {
    bgcolor: BRAND.main,
    color: "#ffffff",
    boxShadow: "none",
    "& .MuiListItemIcon-root": { color: "#ffffff" },
    "& .MuiListItemText-primary": { color: "#ffffff" },
    "&:hover": {
      bgcolor: BRAND.main,
      color: "#ffffff",
      boxShadow: "none",
      "& .MuiListItemIcon-root": { color: "#ffffff" },
      "& .MuiListItemText-primary": { color: "#ffffff" },
    },
    "&.Mui-selected:hover": {
      bgcolor: BRAND.main,
      color: "#ffffff",
      boxShadow: "none",
      "& .MuiListItemIcon-root": { color: "#ffffff" },
      "& .MuiListItemText-primary": { color: "#ffffff" },
    },
    "&.Mui-focusVisible": {
      bgcolor: BRAND.main,
      outline: "none",
      boxShadow: "none",
    },
  };
}

const collapsedTooltipProps = {
  placement: "right",
  arrow: true,
  slotProps: {
    tooltip: {
      sx: {
        fontFamily: FONT_FAMILY,
        fontSize: 16,
        fontWeight: 500,
        py: 0.75,
        px: 1.5,
      },
    },
  },
};

function SidebarNavItem({
  to,
  Icon,
  label,
  badge,
  collapsed,
  end = false,
  onClick,
}) {
  const theme = useTheme();

  const button = (
    <ListItemButton
      component={NavLink}
      to={to}
      end={end}
      onClick={onClick}
      disableRipple
      sx={{
        ...sidebarItemBaseSx(theme, collapsed),
        "&.active": activeItemSx(),
      }}
    >
      <ListItemIcon
        sx={{ minWidth: collapsed ? 0 : 36, justifyContent: "center" }}
      >
        {badge > 0 ? (
          <Badge badgeContent={badge} color="primary" max={999}>
            <Icon />
          </Badge>
        ) : (
          <Icon />
        )}
      </ListItemIcon>
      {!collapsed && (
        <ListItemText
          primary={label}
          primaryTypographyProps={{ fontSize: 13 }}
        />
      )}
    </ListItemButton>
  );

  if (collapsed) {
    return (
      <Tooltip title={label} {...collapsedTooltipProps}>
        <Box component="span" sx={{ display: "block" }}>
          {button}
        </Box>
      </Tooltip>
    );
  }

  return button;
}

export default function Sidebar({
  articles,
  feeds,
  technologyDomains,
  selectedCat,
  onSelectCat,
  collapsed,
  showSettings,
}) {
  const location = useLocation();
  const theme = useTheme();
  const categories = technologyDomainNames(technologyDomains);
  const drawerWidth = collapsed ? LAYOUT.drawerCollapsed : LAYOUT.drawerWidth;

  const bottomItems = [
    ...(showSettings
      ? [{ to: "/settings", Icon: IconSettings, label: "Settings" }]
      : []),
  ];

  const handleCatClick = (cat) => {
    onSelectCat(cat);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          position: "relative",
          borderRight: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
          transition: theme.transitions.create("width"),
          overflowX: "hidden",
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      <Box sx={{ flex: 1, overflowY: "auto", pt: 1 }}>
        <List disablePadding>
          {categories.map((cat, index) => {
            const count = catCount(articles, cat, feeds, technologyDomains);
            const Icon = technologyDomainIcon(index);
            const isActive =
              location.pathname.startsWith("/articles") && selectedCat === cat;

            const item = (
              <ListItemButton
                selected={isActive}
                onClick={() => handleCatClick(cat)}
                disableRipple
                sx={{
                  ...sidebarItemBaseSx(theme, collapsed),
                  "&.Mui-selected": activeItemSx(),
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: collapsed ? 0 : 36,
                    justifyContent: "center",
                  }}
                >
                  {count > 0 ? (
                    <Badge badgeContent={count} color="primary" max={999}>
                      <Icon />
                    </Badge>
                  ) : (
                    <Icon />
                  )}
                </ListItemIcon>
                {!collapsed && (
                  <ListItemText
                    primary={cat}
                    primaryTypographyProps={{ fontSize: 13 }}
                  />
                )}
              </ListItemButton>
            );

            return collapsed ? (
              <Tooltip key={cat} title={cat} {...collapsedTooltipProps}>
                <Box component="span" sx={{ display: "block" }}>
                  {item}
                </Box>
              </Tooltip>
            ) : (
              <Box key={cat} component="span" sx={{ display: "block" }}>
                {item}
              </Box>
            );
          })}
        </List>
      </Box>

      {bottomItems.length > 0 && (
        <Box sx={{ borderTop: 1, borderColor: "divider", py: 1 }}>
          <List disablePadding>
            {bottomItems.map(({ to, Icon, label }) => (
              <SidebarNavItem
                key={to}
                to={to}
                Icon={Icon}
                label={label}
                collapsed={collapsed}
              />
            ))}
          </List>
        </Box>
      )}
    </Drawer>
  );
}
