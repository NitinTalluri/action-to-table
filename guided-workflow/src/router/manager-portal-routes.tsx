import { Navigate, RouteObject } from "react-router";

import ProtectedRoute from "~/components/ProtectedRoute";
import {
  ManagerPortalBookingsRoute,
  SCVRootRoute,
  UnclaimedBookingsRoute,
} from "~/features/manager-portal";
import { ClaimBookingRoute } from "~/features/manager-portal/claim-booking-route";
import { ClaimedBookingsRoute } from "~/features/manager-portal/claimed-bookings-route/claimed-bookings-route";
import { NewBookingRoute } from "~/features/manager-portal/new-booking-route";

export const managerPortalRoutes: RouteObject = {
  path: "/manager-portal",
  element: <ProtectedRoute allowedRoles={["isManager", "isPoolManager"]} />,
  children: [
    {
      element: <ProtectedRoute allowedRoles={["isManager"]} />,
      children: [
        {
          index: true,
          element: <Navigate to={"bookings/unclaimed"} replace />,
        },
        {
          path: "bookings",
          children: [
            { index: true, element: <Navigate to={"unclaimed"} replace /> },
            {
              element: <ManagerPortalBookingsRoute />,
              children: [
                {
                  path: "unclaimed",
                  element: <UnclaimedBookingsRoute />,
                },
                {
                  path: "claimed",
                  element: <ClaimedBookingsRoute />,
                },
              ],
            },
            {
              path: "claim/:bookingContract",
              element: <ClaimBookingRoute />,
            },
            {
              path: "new",
              element: <NewBookingRoute />,
            },
          ],
        },
        {
          path: "pcv",
          element: <SCVRootRoute />,
        },
      ],
    },
    {
      path: "bookings/vendor",
      element: <ProtectedRoute allowedRoles={["isPoolManager"]} />,
      children: [
        {
          element: <ManagerPortalBookingsRoute />,
          children: [
            {
              index: true,
              element: <ClaimedBookingsRoute />,
            },
          ],
        },
      ],
    },
  ],
};
