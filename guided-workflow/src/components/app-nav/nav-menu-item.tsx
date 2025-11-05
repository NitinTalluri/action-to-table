import { MenuItem } from "@mui/material";
import { ReactNode } from "react";
import { Link } from "react-router";

export const NavMenuItem = ({
  to,
  children,
  selected = false,
  onClick,
}: {
  to: string;
  children: ReactNode;
  selected?: boolean;
  onClick?: () => void;
}) => (
  <Link style={{ textDecoration: "none", color: "inherit" }} to={to}>
    <MenuItem sx={[{ px: 4 }]} selected={selected} onClick={onClick}>
      {children}
    </MenuItem>
  </Link>
);
