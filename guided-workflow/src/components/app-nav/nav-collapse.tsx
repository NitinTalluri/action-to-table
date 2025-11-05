import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import { Box, Collapse, List, ListItemButton } from "@mui/material";
import { Fragment, useState } from "react";
import { Link } from "react-router";

import { NavListItemIcon } from "./nav-list-item-icon";
import { NavListItemText } from "./nav-list-item-text";
import { TNavLink } from "./utils";

export const NavCollapse = ({ link }: { link: TNavLink }) => {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Box
        sx={(theme) => ({
          minHeight: 64,
          width: 6,
          background: theme.palette.background.default,
          borderTopRightRadius: 8,
          borderBottomRightRadius: 8,
          position: "absolute",
          visibility: !open && link.isActive ? "visible" : "hidden",
        })}
      ></Box>

      <ListItemButton
        selected={!open && link.isActive}
        sx={(theme) => ({
          minHeight: 64,
          px: 4.5,
          color: link.isActive
            ? theme.palette.common.white
            : theme.palette.grey[50],
        })}
        onClick={() => setOpen((prev) => !prev)}
      >
        {link.icon ? <NavListItemIcon>{link.icon}</NavListItemIcon> : null}
        <NavListItemText primary={link.label} />
        {open ? <ExpandLess /> : <ExpandMore />}
      </ListItemButton>

      {link.children?.length ? (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {link.children.map(
              (child) =>
                !child.isHidden && (
                  <Fragment key={child.label}>
                    <Box
                      sx={(theme) => ({
                        minHeight: 64,
                        width: 6,
                        background: theme.palette.background.default,
                        borderTopRightRadius: 8,
                        borderBottomRightRadius: 8,
                        position: "absolute",
                        visibility: child.isActive ? "visible" : "hidden",
                      })}
                    ></Box>

                    <ListItemButton
                      key={child.label}
                      selected={child.isActive}
                      sx={(theme) => ({
                        minHeight: 64,
                        px: 4.5,
                        pl: 11,
                        color: child.isActive
                          ? theme.palette.common.white
                          : theme.palette.grey[50],
                      })}
                      component={Link}
                      to={child.to || ""}
                    >
                      <NavListItemText primary={child.label} />
                    </ListItemButton>
                  </Fragment>
                ),
            )}
          </List>
        </Collapse>
      ) : null}
    </>
  );
};
