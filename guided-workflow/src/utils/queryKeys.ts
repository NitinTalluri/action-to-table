// To add a query key:
// 1. Add a new key to the rootQueryKey object
// 2. Create a new query key object using the createQueryKeys function

const createQueryKeys = <T>(rootKey: QueryKeyValues) => ({
  all: [rootKey],
  lists: () => [...createQueryKeys(rootKey).all, "list"] as const,
  list: (...filters: T[]) =>
    [...createQueryKeys(rootKey).lists(), ...filters] as const,
  details: () => [...createQueryKeys(rootKey).all, "detail"] as const,
  detail: (...args: T[]) =>
    [...createQueryKeys(rootKey).details(), ...args] as const,
});

export const rootQueryKey = {
  unverifiedBookings: "UNVERIFIED_BOOKINGS",
  verifiedBookings: "VERIFIED_BOOKINGS",
  engagementsUsers: "ENGAGEMENTS_USERS",
  engagementOwners: "ENGAGEMENT_OWNERS",
  engagementLinks: "ENGAGEMENT_LINKS",
  engagements: "ENGAGEMENTS",
  dcTypes: "DC_TYPES",
  contracts: "CONTRACTS",
  canvases: "CANVASES",
  canvasTasks: "CANVAS_TASKS",
  engagementTasks: "ENGAGEMENT_TASKS",
  canvasEvidenceFiles: "CANVAS_EVIDENCE_FILES",
  canvasSnapshotDates: "CANVAS_SNAPSHOT_DATES",
  sdp: "SDP",
  stakeholders: "STAKEHOLDERS",
  workflowTree: "WORKFLOW_TREE",
  workflowNotifications: "WORKFLOW_NOTIFICATIONS",
  tags: "TAGS",
  tagsets: "TAGSETS",
  tml: "TML",
  fileManagement: "FILE_MANAGEMENT",
  userDefinedTypes: "USER_DEFINED_TYPES",
  documentation: "DOCUMENTATION",
  managerPortalUnclaimedBookings: "MANAGER_PORTAL_UNCLAIMED_BOOKINGS",
  managerPortalClaimedBookings: "MANAGER_PORTAL_CLAIMED_BOOKINGS",
  managerPortalClaimedContracts: "MANAGER_PORTAL_CLAIMED_CONTRACTS",
  managerPortalRenewableBookings: "MANAGER_PORTAL_RENEWABLE_BOOKINGS",
  managerPortalAvailableEngagements: "MANAGER_PORTAL_AVAILABLE_ENGAGEMENTS",
  vendorPortalDeliverablesList: "VENDOR_PORTAL_DELIVERABLES_LIST_QUERY",
  support_cases: "SUPPORT_CASES",
  support_agent_cases: "SUPPORT_AGENT_CASES",
  support_available_agents: "SUPPORT_AVAILABLE_AGENTS",
  sprint_goals: "SPRINT_GOALS",
  flowLogging: "FLOW_LOGGING",
  announcements: "ANNOUNCEMENTS",
  deliverables: "DELIVERABLES",
  scheduled_deliverables: "SCHEDULED_DELIVERABLES",
  active_deliverables: "ACTIVE_DELIVERABLES",
  closed_deliverables: "CLOSED_DELIVERABLES",
  time_tracking: "TIME_TRACKING",
  time_tracking_summary: "TIME_TRACKING_SUMMARY",
  manager_portal_scv: "MANAGER_PORTAL_SCV",
  macd_schemas: "MACD_SCHEMAS",
  macd_input: "MACD_INPUT",
  thoughtspot: "THOUGHTSPOT",
  macd_historical: "MACD_HISTORICAL",
} as const;

type QueryKeys = typeof rootQueryKey;
type QueryKeyValues = QueryKeys[keyof QueryKeys];

export const unverifiedBookingsQueryKeys = createQueryKeys(
  rootQueryKey.unverifiedBookings,
);
export const verifiedBookingsQueryKeys = createQueryKeys(
  rootQueryKey.verifiedBookings,
);
export const engagementsUsersQueryKeys = createQueryKeys(
  rootQueryKey.engagementsUsers,
);
export const engagementLinksQueryKeys = createQueryKeys(
  rootQueryKey.engagementLinks,
);
export const engagementsQueryKeys = createQueryKeys(rootQueryKey.engagements);
export const engagementOwnersQueryKeys = createQueryKeys(
  rootQueryKey.engagementOwners,
);
export const dcTypesQueryKeys = createQueryKeys(rootQueryKey.dcTypes);
export const contractsQueryKeys = createQueryKeys(rootQueryKey.contracts);
export const canvasesQueryKeys = createQueryKeys(rootQueryKey.canvases);
export const engagementTasksQueryKeys = createQueryKeys(
  rootQueryKey.engagementTasks,
);
export const canvasTasksQueryKeyList = (
  canvasId: number,
  engagementId: number,
) =>
  engagementTasksQueryKeys.list(engagementId, [
    rootQueryKey.canvasTasks,
    canvasId,
  ]);

export const canvasEvidenceFilesQueryKeys = createQueryKeys(
  rootQueryKey.canvasEvidenceFiles,
);
export const canvasSnapshotDatesQueryKeys = createQueryKeys(
  rootQueryKey.canvasSnapshotDates,
);
export const stakeholdersQueryKeys = createQueryKeys(rootQueryKey.stakeholders);
export const workflowTreeQueryKeys = createQueryKeys(rootQueryKey.workflowTree);
export const workflowNotificationsQueryKeys = createQueryKeys(
  rootQueryKey.workflowNotifications,
);
export const tagsQueryKeys = createQueryKeys(rootQueryKey.tags);
export const tagsetsQueryKeys = createQueryKeys(rootQueryKey.tagsets);
export const tmlQueryKeys = createQueryKeys(rootQueryKey.tml);
export const fileManagementQueryKeys = createQueryKeys(
  rootQueryKey.fileManagement,
);
export const userDefinedTypesQueryKeys = createQueryKeys(
  rootQueryKey.userDefinedTypes,
);
export const documentationQueryKeys = createQueryKeys(
  rootQueryKey.documentation,
);
export const managerPortalUnclaimedBookingsQueryKeys = createQueryKeys(
  rootQueryKey.managerPortalUnclaimedBookings,
);
export const managerPortalClaimedBookingsQueryKeys = createQueryKeys(
  rootQueryKey.managerPortalClaimedBookings,
);
export const managerPortalClaimedContractsQueryKeys = createQueryKeys(
  rootQueryKey.managerPortalClaimedContracts,
);
export const managerPortalRenewableBookingsQueryKeys = createQueryKeys(
  rootQueryKey.managerPortalRenewableBookings,
);
export const sdpQueryKeys = createQueryKeys(rootQueryKey.sdp);
export const managerPortalAvailableEngagementsQueryKeys = createQueryKeys(
  rootQueryKey.managerPortalAvailableEngagements,
);
export const vendorPortalDeliverablesListQueryKeys = createQueryKeys(
  rootQueryKey.vendorPortalDeliverablesList,
);
export const supportCasesQueryKeys = createQueryKeys(
  rootQueryKey.support_cases,
);
export const supportAgentCasesQueryKeys = createQueryKeys(
  rootQueryKey.support_agent_cases,
);
export const supportAvailableAgentsQueryKeys = createQueryKeys(
  rootQueryKey.support_available_agents,
);
export const sprintGoalsQueryKeys = createQueryKeys(rootQueryKey.sprint_goals);
export const announcementsQueryKeys = createQueryKeys(
  rootQueryKey.announcements,
);
export const deliverablesQueryKeys = createQueryKeys(rootQueryKey.deliverables);
export const scheduledDeliverablesQueryKeys = createQueryKeys(
  rootQueryKey.scheduled_deliverables,
);
export const activeDeliverablesQueryKeys = createQueryKeys(
  rootQueryKey.active_deliverables,
);
export const closedDeliverablesQueryKeys = createQueryKeys(
  rootQueryKey.closed_deliverables,
);
export const timeTrackingQueryKeys = createQueryKeys(
  rootQueryKey.time_tracking,
);
export const timeTrackingSummaryQueryKeys = createQueryKeys(
  rootQueryKey.time_tracking_summary,
);
export const superCustomeViewQueryKeys = createQueryKeys(
  rootQueryKey.manager_portal_scv,
);
export const macdSchemasQueryKeys = createQueryKeys(rootQueryKey.macd_schemas);
export const macdInputsQueryKeys = createQueryKeys(rootQueryKey.macd_input);
export const thoughtspotQueryKeys = createQueryKeys(rootQueryKey.thoughtspot);
export const macdHistoricalQueryKeys = createQueryKeys(
  rootQueryKey.macd_historical,
);
