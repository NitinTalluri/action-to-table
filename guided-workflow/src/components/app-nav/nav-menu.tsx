import {
  Box,
  Divider,
  ListItem,
  ListItemButton,
  Popover,
  Tooltip,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { NavListItemIcon } from "./nav-list-item-icon";
import { NavMenuItem } from "./nav-menu-item";
import { TNavLink } from "./utils";

export const NavMenu = ({ link }: { link: TNavLink }) => {
  const [anchorEl, setAnchorEl] = useState<HTMLDivElement | null>(null);
  const open = Boolean(anchorEl);
  const popoverId = open ? "popover" : undefined;
  return (
    <ListItem disablePadding>
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

      <Tooltip arrow placement="right" title={link.label}>
        <ListItemButton
          sx={(theme) => ({
            minHeight: 64,
            px: 4.5,
            color: link.isActive
              ? theme.palette.common.white
              : theme.palette.grey[50],
          })}
          onClick={(e) => setAnchorEl(e.currentTarget)}
        >
          {link.icon ? (
            <NavListItemIcon expanded={false}>{link.icon}</NavListItemIcon>
          ) : (
            <div></div>
          )}
        </ListItemButton>
      </Tooltip>

      <Popover
        id={popoverId}
        open={open}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{
          vertical: "center",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "left",
        }}
        slotProps={{
          paper: {
            style: { marginLeft: 4 },
          },
        }}
      >
        <Box>
          <Typography
            sx={(theme) => ({
              paddingX: 2,
              paddingY: 1,
              color: theme.palette.primary.main,
              fontWeight: 500,
            })}
          >
            {link.label}
          </Typography>

          <Divider />

          {link.children?.map(
            (item) =>
              !item.isHidden && (
                <NavMenuItem
                  key={item.label}
                  onClick={() => setAnchorEl(null)}
                  selected={item.isActive}
                  to={item.to || ""}
                >
                  {item.label}
                </NavMenuItem>
              ),
          )}
        </Box>
      </Popover>
    </ListItem>
  );
};
