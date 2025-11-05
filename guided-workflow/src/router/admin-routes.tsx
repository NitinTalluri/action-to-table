import { Navigate, RouteObject } from "react-router";

import ProtectedRoute from "~/components/ProtectedRoute";
import GlobalTagset from "~/features/global-tagset/GlobalTagset";

import { sdpRoutes } from "./sdp-routes";

export const adminRoutes: RouteObject = {
  path: "admin",
  element: <ProtectedRoute allowedRoles={["isAdmin"]} />,
  children: [
    {
      index: true,
      element: <Navigate to={"global-tagset"} replace />,
    },

    {
      path: "global-tagset",
      element: <GlobalTagset />,
    },

    sdpRoutes,
  ],
};
