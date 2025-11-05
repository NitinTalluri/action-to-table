import { Navigate, RouteObject } from "react-router";

import { NotFound } from "~/components/not-found";
import ProtectedRoute from "~/components/ProtectedRoute";
import { AddOwnersRoute } from "~/features/admin/add-owners-route";
import { DeletedCanvasesTable } from "~/features/admin/deleted-canvases-table";
import { DeletedEngagementsTable } from "~/features/admin/deleted-engagements-table";
import { DeletedTagsTable } from "~/features/admin/deleted-tags-table";
import { DeletedTagsetsTable } from "~/features/admin/deleted-tagsets-table";
import SprintGoalsRoute from "~/features/admin/sprint-goals-route";
import { UndeleteRoute } from "~/features/admin/undelete-route";
import {
  AnnouncementDetailRoute,
  AnnouncementEditRoute,
  AnnouncementsRoute,
  CreateAnnouncementRoute,
} from "~/features/announcements";
import { CreateCase } from "~/features/case/create-case";
import { SupportRoute } from "~/features/support-route";
import {
  AgentCasesRoute,
  CasesRoute,
  MetricsRoute,
  SupportHomeRoute,
} from "~/features/support-route/sub-routes";
import { AgentCaseDetailRoute } from "~/features/support-route/sub-routes/agent-case-detail-route";
import { CaseDetailRoute } from "~/features/support-route/sub-routes/case-detail-route";

import { documentationRoutes } from "./documentation-routes";

export const supportRoutes: RouteObject = {
  path: "/support",
  element: <SupportRoute />,
  children: [
    { index: true, element: <SupportHomeRoute /> },
    {
      path: "metrics",
      element: <MetricsRoute />,
    },
    {
      path: "admin",
      element: <ProtectedRoute allowedRoles={["isSupport"]} />,
      children: [
        {
          path: "add-owners",
          element: <AddOwnersRoute />,
        },
        {
          path: "undelete",
          element: <UndeleteRoute />,
          children: [
            {
              index: true,
              element: <Navigate to="engagement" replace />,
            },
            {
              path: "engagement",
              element: <DeletedEngagementsTable />,
            },
            {
              path: "canvases",
              element: <DeletedCanvasesTable />,
            },
            {
              path: "tagsets",
              element: <DeletedTagsetsTable />,
            },
            {
              path: "tags",
              element: <DeletedTagsTable />,
            },
          ],
        },
        {
          path: "sprint-goals",
          element: <SprintGoalsRoute />,
        },
      ],
    },
    {
      path: "cases",
      children: [
        { index: true, element: <CasesRoute /> },
        {
          path: ":caseId",
          element: <CaseDetailRoute />,
        },
        {
          path: "create",
          element: <CreateCase />,
        },
        {
          path: "agent",
          element: <ProtectedRoute allowedRoles={["isSupport"]} />,
          children: [
            {
              index: true,
              element: <AgentCasesRoute />,
            },
            {
              path: ":caseId",
              element: <AgentCaseDetailRoute />,
            },
          ],
        },
      ],
    },

    {
      path: "announcements",
      children: [
        { index: true, element: <AnnouncementsRoute /> },
        {
          path: ":announcementId",
          children: [
            { index: true, element: <AnnouncementDetailRoute /> },
            {
              path: "edit",
              element: <ProtectedRoute allowedRoles={["isSupport"]} />,
              children: [{ index: true, element: <AnnouncementEditRoute /> }],
            },
          ],
        },
        {
          path: "create",
          element: <ProtectedRoute allowedRoles={["isSupport"]} />,
          children: [{ index: true, element: <CreateAnnouncementRoute /> }],
        },
      ],
    },
    ...documentationRoutes,
    {
      path: "*",
      element: <NotFound />,
    },
  ],
};
