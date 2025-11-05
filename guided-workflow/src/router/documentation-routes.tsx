import { type RouteObject } from "react-router";

import ProtectedRoute from "~/components/ProtectedRoute";
import {
  DocumentationDetailRoute,
  DocumentationEditRoute,
} from "~/features/documentation-routes";
import {
  WorkflowDocumentationDetailRoute,
  WorkflowDocumentationHome,
} from "~/features/workflow-documentation";
import { WorkflowDocumentationAdminRoute } from "~/features/workflow-documentation/workflow-documentation-admin";
import { WorkflowDocumentationEditRoute } from "~/features/workflow-documentation/workflow-documentation-edit-route";

export const documentationRoutes: RouteObject[] = [
  {
    path: "documentation/:docType",
    children: [
      { index: true, element: <DocumentationDetailRoute /> },
      {
        path: "edit",
        element: <ProtectedRoute allowedRoles={["isAdmin"]} />,
        children: [{ index: true, element: <DocumentationEditRoute /> }],
      },
    ],
  },
  {
    path: "workflows",
    children: [
      { index: true, element: <WorkflowDocumentationHome /> },
      {
        path: ":workflowUiEnum",
        children: [
          { index: true, element: <WorkflowDocumentationDetailRoute /> },
          {
            path: "edit",
            element: <ProtectedRoute allowedRoles={["isAdmin"]} />,
            children: [
              { index: true, element: <WorkflowDocumentationEditRoute /> },
            ],
          },
          {
            path: "admin",
            element: <ProtectedRoute allowedRoles={["isAdmin"]} />,
            children: [
              { index: true, element: <WorkflowDocumentationAdminRoute /> },
            ],
          },
        ],
      },
    ],
  },
];
