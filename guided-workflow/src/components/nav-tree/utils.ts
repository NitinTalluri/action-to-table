import { z } from "zod";

import { TSummaryNotification, WorkflowUiEnum } from "~/domain/Workflows";

// as const make these arrays more accurate when interpreted as a type below
const categoryFilters = ["result", "task", "error", "pending"] as const;
export const dateFilters = [
  "last_hour",
  "last_24_hours",
  "last_week",
  "last_month",
  "",
] as const;
export const viewFilters = ["all_users", ""] as const;

export const drawerWidth = 240;

// used in the filter select and as url search params
export const FILTER_VIEW_SEARCH_PARAM = "filter-view";
export const FILTER_CATEGORY_SEARCH_PARAM = "filter-category";
export const FILTER_DATES_SEARCH_PARAM = "filter-dates";
export const SELECTED_CATEGORY_SEARCH_PARAM = "selected-category";
export const AUDIT_LOG_SEARCH_PARAM = "audit-log";

export type TFilters = {
  view: (typeof viewFilters)[number];
  category: (typeof categoryFilters)[number][];
  dates: (typeof dateFilters)[number];
};

export interface RenderTree {
  id: string;
  name: string;
  to?: string;
  notifications?: TSummaryNotification[];
  children?: RenderTree[];
}

// Type check for readback onChange
export const isCategory = (
  value: string,
): value is TFilters["category"][number] =>
  categoryFilters.includes(value as (typeof categoryFilters)[number]);

// Type check for readback onChange
export const isDate = (value: string): value is TFilters["dates"] =>
  dateFilters.includes(value as (typeof dateFilters)[number]);

// Type check for readback onChange
export const isView = (value: string): value is TFilters["view"] =>
  viewFilters.includes(value as (typeof viewFilters)[number]);

// recursively check if a node has a matching to prop
export const hasMatchingTo = (name: string, item: RenderTree): boolean => {
  if (item.to === name) {
    return true;
  }
  if (item.children) {
    return item.children.some((child) => hasMatchingTo(name, child));
  }
  return false;
};

// Gets the nodeIds that match the current route
export const getRoutedNodeIds = (
  items: RenderTree[],
  name: string,
): string[] => {
  const ids: string[] = [];
  items.forEach((item) => {
    if (hasMatchingTo(name || "", item)) {
      ids.push(item.id);
      if (item.children) {
        ids.push(...getRoutedNodeIds(item.children, name));
      }
    }
  });
  return ids;
};

export const chipColor = {
  result: "success",
  task: "warning",
  error: "error",
  pending: "info",
} as const;

const oneSecond = 1000;
const oneMinute = oneSecond * 60;
const oneHour = oneMinute * 60;
const oneDay = oneHour * 24;

// some dates used when filtering
const now = new Date();
export const lastHour = new Date(now.getTime() - oneHour);
export const last24Hours = new Date(now.getTime() - oneDay);
export const lastWeek = new Date(now.getTime() - 7 * oneDay);
export const lastMonth = new Date(now.getTime() - 30 * oneDay);

export const notificationTotalsByDate = (
  item: RenderTree[],
  view: TFilters["view"],
  range: TFilters["dates"],
  dc_user_id?: number,
  category?: TFilters["category"][number],
  expanded = false,
) => {
  const reduced = item.reduce((acc, node) => {
    let total = 0;
    const notifications = node?.notifications || [];

    const notificationFilterUsers = notifications.filter(
      (notification) =>
        !dc_user_id ||
        view === "all_users" ||
        notification.dc_user_id === dc_user_id,
    );

    const notificationsTotal = notificationFilterUsers.reduce(
      (acc, notification) => {
        const date = new Date(
          notification.update_dtm || notification.create_dtm,
        );
        const isCategory = category
          ? notification.notification_category === category
          : true;
        if (range === "last_hour") {
          return date > lastHour && isCategory ? acc + 1 : acc;
        }
        if (range === "last_24_hours") {
          return date > last24Hours && isCategory ? acc + 1 : acc;
        }
        if (range === "last_week") {
          return date > lastWeek && isCategory ? acc + 1 : acc;
        }
        if (range === "last_month") {
          return date > lastMonth && isCategory ? acc + 1 : acc;
        }
        return isCategory ? acc + 1 : acc;
      },
      0,
    );
    total += notificationsTotal;

    // if the node has children and is not expanded, add children
    if (node.children && !expanded) {
      total += notificationTotalsByDate(
        (item = node.children),
        view,
        range,
        dc_user_id,
        category,
      );
    }
    return acc + total;
  }, 0);
  return reduced;
};

export const dateTotals = (
  item: RenderTree[],
  view: TFilters["view"],
  dc_user_id?: number,
) => {
  const totals = {
    last_hour: notificationTotalsByDate(item, view, "last_hour", dc_user_id),
    last_24_hours: notificationTotalsByDate(
      item,
      view,
      "last_24_hours",
      dc_user_id,
    ),
    last_week: notificationTotalsByDate(item, view, "last_week", dc_user_id),
    last_month: notificationTotalsByDate(item, view, "last_month", dc_user_id),
  };
  return totals;
};

// category totals consider dates whereas dateTotals do not
export const categoryTotals = (
  item: RenderTree[],
  date: TFilters["dates"],
  view: TFilters["view"],
  dc_user_id?: number,
) => {
  const totals = {
    error: notificationTotalsByDate(item, view, date, dc_user_id, "error"),
    result: notificationTotalsByDate(item, view, date, dc_user_id, "result"),
    task: notificationTotalsByDate(item, view, date, dc_user_id, "task"),
    pending: notificationTotalsByDate(item, view, date, dc_user_id, "pending"),
  };
  return totals;
};

export const getCategoryTotal = (
  item: RenderTree,
  filters: TFilters,
  expanded: boolean,
  dc_user_id?: number,
) => {
  const totals = categoryFilters.reduce(
    (acc, category) => {
      const sumByCategory = notificationTotalsByDate(
        [item],
        filters.view,
        filters.dates,
        dc_user_id,
        category,
        expanded,
      );
      const hasFilterApplied =
        Boolean(filters.category.length) &&
        !filters.category.includes(category);
      if (hasFilterApplied) {
        return {
          ...acc,
          [category]: 0,
        };
      }
      return {
        ...acc,
        [category]: sumByCategory,
      };
    },
    {} as Record<(typeof categoryFilters)[number], number>,
  );
  return totals;
};

export const getUiEnumFromPathname = (pathname: string) => {
  const paths = pathname.split("/").filter(Boolean);
  const path = paths.find((p) => WorkflowUiEnum.safeParse(p).success);
  if (path) {
    return path as z.infer<typeof WorkflowUiEnum>;
  }
};

export const findTreeNodeFromUiEnum = (
  tree: RenderTree[],
  uiEnum?: z.infer<typeof WorkflowUiEnum>,
): RenderTree | undefined => {
  // recursively search for the node with the matching ui_enum
  const findNode = (node: RenderTree): RenderTree | undefined => {
    if (node.to === uiEnum) {
      return node;
    }
    if (node.children) {
      return node.children.map(findNode).find(Boolean);
    }
  };
  return tree.map(findNode).find(Boolean);
};

export const getNotificationsByDateFilter = (
  notifications: TSummaryNotification[],
  dateFilter: TFilters["dates"],
) => {
  return notifications.filter((notification) => {
    const date = new Date(notification.update_dtm || notification.create_dtm);
    if (dateFilter === "last_hour") {
      return date > lastHour;
    }
    if (dateFilter === "last_24_hours") {
      return date > last24Hours;
    }
    if (dateFilter === "last_week") {
      return date > lastWeek;
    }
    if (dateFilter === "last_month") {
      return date > lastMonth;
    }
    return true;
  });
};
