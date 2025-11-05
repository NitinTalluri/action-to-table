import ListItemIcon, { ListItemIconProps } from "@mui/material/ListItemIcon";
import { styled } from "@mui/material/styles";

interface NavListItemIconProps extends ListItemIconProps {
  expanded?: boolean;
}

export const NavListItemIcon = styled(ListItemIcon, {
  shouldForwardProp: (prop) => prop !== "expanded",
})<NavListItemIconProps>(({ expanded = true }) => ({
  color: "inherit",
  minWidth: 0,
  justifyContent: "center",
  marginRight: expanded ? 16 : "auto",
}));
