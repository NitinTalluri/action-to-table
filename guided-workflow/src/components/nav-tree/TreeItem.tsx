import { Box, Typography } from "@mui/material";
import { TreeItem as XTreeItem } from "@mui/x-tree-view";
import { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { TreeItemNotifications } from "./TreeItemNotifications";
import {
  getCategoryTotal,
  RenderTree,
  SELECTED_CATEGORY_SEARCH_PARAM,
  TFilters,
} from "./utils";

export const TreeItem = ({
  dc_user_id,
  item,
  filters,
  expanded,
  children,
}: {
  dc_user_id?: number;
  item: RenderTree;
  filters: TFilters;
  expanded: boolean;
  children: ReactNode;
}) => {
  const navigate = useNavigate();
  const { search, pathname } = useLocation();
  const notifications = getCategoryTotal(item, filters, expanded, dc_user_id);

  const handleClick = (priority: TFilters["category"][number]) => {
    if (!item.to) {
      return;
    }
    const urlSearchParams = new URLSearchParams(search);
    urlSearchParams.set(SELECTED_CATEGORY_SEARCH_PARAM, priority);
    navigate({
      pathname: `events/${item.to}/`,
      search: urlSearchParams.toString(),
    });
  };

  const isRoutedTo = pathname.split("/").some((path) => path === item.to);
  const childIsActive =
    item.children?.some((child) =>
      pathname.split("/").some((path) => path === child.to),
    ) || false;
  const showActiveDot = isRoutedTo || (!expanded && childIsActive);
  return (
    <XTreeItem
      key={item.id}
      itemId={item.id}
      label={
        <OptionalTo to={item.to}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              position: "relative",
              p: 0.5,
              pr: 0,
            }}
          >
            {showActiveDot ? (
              <Box
                sx={(theme) => ({
                  position: "absolute",
                  right: "100%",
                  width: ".5rem",
                  height: ".5rem",
                  backgroundColor: theme.palette.primary.main,
                  borderRadius: "50%",
                })}
              />
            ) : null}
            <Typography variant="body1" sx={{ flexGrow: 1 }}>
              {item.name}
            </Typography>
            <Box>
              <TreeItemNotifications
                notifications={notifications}
                onClick={item?.to ? handleClick : undefined}
              />
            </Box>
          </Box>
        </OptionalTo>
      }
    >
      {children}
    </XTreeItem>
  );
};

// if a to prop is passed, wrap the label in a Link
const OptionalTo = ({ to, children }: { to?: string; children: ReactNode }) => {
  const { search } = useLocation();
  const urlSearchParams = new URLSearchParams(search);
  // remove tab search param when navigating to a different route
  urlSearchParams.delete(SELECTED_CATEGORY_SEARCH_PARAM);

  if (typeof to === "string") {
    return (
      <Link
        style={{ textDecoration: "none", color: "inherit", display: "block" }}
        // preserve any current query params
        to={{ pathname: to, search: urlSearchParams.toString() }}
      >
        {children}
      </Link>
    );
  }
  return <>{children}</>;
};
