import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useParams, useSearchParams } from "react-router";

import { getWorkflowNotifications, getWorkflowTree } from "~/api/workflows";
import { TWorkflowTree } from "~/domain/Workflows";
import {
  workflowNotificationsQueryKeys,
  workflowTreeQueryKeys,
} from "~/utils/queryKeys";

import {
  AUDIT_LOG_SEARCH_PARAM,
  FILTER_CATEGORY_SEARCH_PARAM,
  FILTER_DATES_SEARCH_PARAM,
  FILTER_VIEW_SEARCH_PARAM,
  RenderTree,
  TFilters,
} from "../utils";
import {
  assembleChildren,
  attachNotifications,
  filterDuplicationsTree,
  sortTree,
} from "./utils";

const today = new Date();
// defaults to 6 months ago
const DEFAULT_NOTIFICATIONS_AGO = new Date(
  today.getFullYear(),
  today.getMonth() - 6,
  today.getDate(),
);

export const useTreeConfig = () => {
  const { engagementId } = useParams();
  const [searchParams] = useSearchParams();

  const auditLog = searchParams.get(AUDIT_LOG_SEARCH_PARAM) || "";
  const filterView = searchParams.get(FILTER_VIEW_SEARCH_PARAM) || "";
  const filterCategory =
    searchParams.getAll(FILTER_CATEGORY_SEARCH_PARAM) || "";
  const filterDates = searchParams.get(FILTER_DATES_SEARCH_PARAM) || "";

  const filters: TFilters = {
    view: filterView as TFilters["view"],
    category: filterCategory as TFilters["category"],
    dates: filterDates as TFilters["dates"],
  };

  const generateTreeConfig = (tree: TWorkflowTree): RenderTree[] => {
    // create the tree config
    const treeConfig: RenderTree[] = tree.map((node) => {
      return {
        id: node.tree_id.toString(),
        name: node.action_label,
        ...(node.ui_enum ? { to: node.ui_enum } : {}),
        children: node.child_ids.length
          ? assembleChildren(tree, node.tree_id)
          : [],
      };
    });
    // filter out duplications
    const filteredTree = filterDuplicationsTree(treeConfig);
    // sort the tree by label
    const sortedTree = sortTree(filteredTree);
    return sortedTree;
  };

  const { data: treeConfig, status: treeStatus } = useQuery({
    queryKey: workflowTreeQueryKeys.lists(),
    queryFn: async () => {
      const treeData = await getWorkflowTree();
      return generateTreeConfig(treeData);
    },
    staleTime: Infinity,
  });

  const sixMonthsAgo = DEFAULT_NOTIFICATIONS_AGO.toISOString();
  const dateFilter = {
    last_hour: new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
      today.getHours() - 1,
    ).toISOString(),
    last_24_hours: new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
      today.getHours() - 24,
    ).toISOString(),
    last_week: new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() - 7,
    ).toISOString(),
    last_month: new Date(
      today.getFullYear(),
      today.getMonth() - 1,
      today.getDate(),
    ).toISOString(),
    "": sixMonthsAgo,
  }[filters.dates];

  const lastActivity = auditLog === "true" ? "" : dateFilter;

  const {
    data: treeNotifications,
    status: notificationsStatus,
    isFetching: isFetchingNotification,
  } = useQuery({
    queryKey: workflowNotificationsQueryKeys.list(engagementId, lastActivity),
    queryFn: async () => {
      const notificationsPromise = getWorkflowNotifications(
        Number(engagementId),
        lastActivity,
      );
      return await notificationsPromise;
    },
    enabled: Boolean(engagementId),
    retry: false,
  });

  // attach notifications to the tree
  const treeWithNotifications = useMemo(
    () => attachNotifications(treeConfig || [], treeNotifications || []),
    [treeConfig, treeNotifications],
  );

  return {
    treeConfig: treeWithNotifications,
    treeConfigRaw: treeConfig,
    treeStatus,
    notificationsStatus,
    isFetchingNotification,
  };
};
