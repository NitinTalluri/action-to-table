import { Navigate, type RouteObject } from "react-router";

import {
  CreateDeliverable,
  CreateSubtask,
  CreateTask,
  EditDeliverable,
  EditSubtask,
  EditTask,
  SDPParentRoute,
  ViewDeliverable,
  ViewSubtask,
  ViewTask,
} from "~/features/sdp";
import { SDPTable } from "~/features/sdp/sdp-table";

export const sdpRoutes: RouteObject = {
  path: "sdp",
  element: <SDPParentRoute />,
  children: [
    {
      index: true,
      element: <SDPTable />,
    },

    {
      path: "subtask",
      children: [
        {
          index: true,
          element: <Navigate to=".." replace />,
        },
        {
          path: ":id",
          children: [
            {
              index: true,
              element: <ViewSubtask />,
            },
            {
              path: "edit",
              element: <EditSubtask />,
            },
          ],
        },
        {
          path: "create",
          element: <CreateSubtask />,
        },
      ],
    },

    {
      path: "task",
      children: [
        {
          index: true,
          element: <Navigate to=".." replace />,
        },
        {
          path: ":id",
          children: [
            {
              index: true,
              element: <ViewTask />,
            },
            {
              path: "edit",
              element: <EditTask />,
            },
          ],
        },
        {
          path: "create",
          element: <CreateTask />,
        },
      ],
    },

    {
      path: "deliverable",
      children: [
        {
          index: true,
          element: <Navigate to=".." replace />,
        },
        {
          path: ":id",
          children: [
            {
              index: true,
              element: <ViewDeliverable />,
            },
            {
              path: "edit",
              element: <EditDeliverable />,
            },
          ],
        },
        {
          path: "create",
          element: <CreateDeliverable />,
        },
      ],
    },
  ],
};
