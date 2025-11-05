import { Box, Drawer, useMediaQuery, useTheme } from "@mui/material";
import { Outlet, useLocation } from "react-router";

import { SidebarNav } from "./components/app-nav";
import { navLinks } from "./components/app-nav/nav-links";
import useLocalStorage from "./hooks/useLocalStorage";
import useUserContext from "./hooks/users/useUserContext";

export const RootRoute = () => {
  const user = useUserContext();
  const { pathname } = useLocation();

  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [isExpanded, setIsExpanded] = useLocalStorage({
    key: "is-side-nav-expanded",
    initialValue: isDesktop,
  });

  const drawerWidth = isExpanded ? 300 : 96;
  return (
    <Box
      sx={{
        display: "flex",
        backgroundColor: theme.palette.grey[50],
      }}
    >
      <Drawer
        variant="permanent"
        sx={(theme) => ({
          width: drawerWidth,
          zIndex: 2,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            border: "none",
            backgroundColor: theme.palette.primary.main,
            color: theme.palette.primary.contrastText,
            width: drawerWidth,
            boxSizing: "border-box",
            boxShadow: "10px 0px 10px -3px rgb(0 0 0 / 0.2)",
            transition: theme.transitions.create(["width", "margin"], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            overflow: "visible",
          },
        })}
      >
        <SidebarNav
          links={navLinks({ user, pathname })}
          expanded={isExpanded}
          onExpandChange={setIsExpanded}
        />
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          paddingX: 3,
          overflow: "auto",
        }}
      >
        <Box sx={{ minHeight: "100vh" }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};
