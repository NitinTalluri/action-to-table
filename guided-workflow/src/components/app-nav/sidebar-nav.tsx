import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import LiveHelpIcon from "@mui/icons-material/LiveHelp";
import LogoutIcon from "@mui/icons-material/Logout";
import {
  Box,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  Stack,
  Tooltip,
} from "@mui/material";
import { Auth } from "aws-amplify";
import { Dispatch, SetStateAction } from "react";
import { Link, useLocation } from "react-router";
import { toast } from "sonner";

import { getErrorMessage } from "~/utils/getErrorMessage";

import CiscoIcon from "../Icons/CiscoIcon";
import { AppTitle } from "./app-title";
import { NavCollapse } from "./nav-collapse";
import { NavListItemIcon } from "./nav-list-item-icon";
import { NavListItemText } from "./nav-list-item-text";
import { NavMenu } from "./nav-menu";
import { TNavLink } from "./utils";

export const SidebarNav = ({
  links,
  expanded,
  onExpandChange,
}: {
  links: TNavLink[];
  expanded: boolean;
  onExpandChange: Dispatch<SetStateAction<boolean>>;
}) => {
  const { pathname } = useLocation();
  return (
    <Stack
      justifyContent="space-between"
      gap={1}
      height="100%"
      sx={{ overflow: "auto" }}
    >
      <Stack>
        {/* HEADER */}
        {expanded ? (
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="center"
            paddingX={1}
          >
            <Stack direction="row" alignItems="center" justifyContent="center">
              <CiscoIcon
                sx={(theme) => ({
                  fontSize: "5rem",
                  color: theme.palette.primary.contrastText,
                })}
              />
              <AppTitle />
            </Stack>

            <IconButton
              size="small"
              sx={(theme) => ({
                background: theme.palette.background.default,
                position: "absolute",
                left: "100%",
                transform: "translateX(-50%)",
                color: theme.palette.primary.main,
                boxShadow: "5px 0px 5px -3px rgb(0 0 0 / 0.2)",
                "&:hover": { background: theme.palette.background.default },
              })}
              onClick={() => onExpandChange((prev) => !prev)}
            >
              <ChevronLeftIcon />
            </IconButton>
          </Stack>
        ) : (
          <>
            <Stack direction="row" justifyContent="center" p={1}>
              <IconButton
                color="inherit"
                size="small"
                sx={(theme) => ({
                  border: `1px solid ${theme.palette.primary.contrastText}`,
                })}
                onClick={() => onExpandChange((prev) => !prev)}
              >
                <ChevronRightIcon />
              </IconButton>
            </Stack>
            <CiscoIcon
              sx={(theme) => ({
                alignSelf: "center",
                fontSize: "5rem",
                color: theme.palette.primary.contrastText,
              })}
            />
          </>
        )}

        {/* Upper Links */}
        <List
          sx={() => ({
            marginTop: 2,
          })}
        >
          {links.map((link) => {
            if (link.isHidden) return null;

            if (link.children?.length) {
              if (expanded) {
                return <NavCollapse key={link.label} link={link} />;
              }
              return <NavMenu key={link.label} link={link} />;
            }

            return (
              <ListItem disablePadding key={link.label}>
                <Box
                  sx={(theme) => ({
                    minHeight: 64,
                    width: 6,
                    background: theme.palette.background.default,
                    borderTopRightRadius: 8,
                    borderBottomRightRadius: 8,
                    position: "absolute",
                    visibility: link.isActive ? "visible" : "hidden",
                  })}
                ></Box>

                <Tooltip
                  arrow
                  placement="right"
                  title={expanded ? undefined : link.label}
                >
                  <ListItemButton
                    sx={(theme) => ({
                      minHeight: 64,
                      px: 4.5,
                      color: link.isActive
                        ? theme.palette.common.white
                        : theme.palette.grey[50],
                    })}
                    component={Link}
                    to={link.to || ""}
                  >
                    {link.icon ? (
                      <NavListItemIcon expanded={expanded}>
                        {link.icon}
                      </NavListItemIcon>
                    ) : null}

                    {expanded ? <NavListItemText primary={link.label} /> : null}
                  </ListItemButton>
                </Tooltip>
              </ListItem>
            );
          })}
        </List>
      </Stack>
      <List sx={[{ marginBottom: 2 }]}>
        {["/support", "/support/cases/create"].every(
          (path) => path !== pathname,
        ) ? (
          <ListItem disablePadding>
            <Tooltip
              arrow
              placement="right"
              title={expanded ? undefined : "Open a case"}
            >
              <ListItemButton
                component={Link}
                to={{
                  pathname: "/support/cases/create",
                  search: `?path=${pathname}`,
                }}
                sx={[
                  {
                    minHeight: 64,
                    px: 6,
                  },
                  expanded
                    ? {
                        justifyContent: "initial",
                      }
                    : {
                        justifyContent: "center",
                      },
                ]}
              >
                <NavListItemIcon expanded={expanded}>
                  <LiveHelpIcon />
                </NavListItemIcon>
                {expanded ? <NavListItemText primary="Open a case" /> : null}
              </ListItemButton>
            </Tooltip>
          </ListItem>
        ) : null}
        <ListItem disablePadding>
          <Tooltip
            arrow
            placement="right"
            title={expanded ? undefined : "Log out"}
          >
            <ListItemButton
              onClick={async () => {
                toast.promise(Auth.signOut(), {
                  loading: "Logging out...",
                  success: "Logged out successfully",
                  error: (error) => getErrorMessage("Failed to log out", error),
                });
              }}
              sx={[
                {
                  minHeight: 64,
                  px: 6,
                },
                expanded
                  ? {
                      justifyContent: "initial",
                    }
                  : {
                      justifyContent: "center",
                    },
              ]}
            >
              <NavListItemIcon expanded={expanded}>
                <LogoutIcon />
              </NavListItemIcon>
              {expanded ? <NavListItemText primary="Log out" /> : null}
            </ListItemButton>
          </Tooltip>
        </ListItem>
      </List>
    </Stack>
  );
};
