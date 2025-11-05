import { Navigate, RouteObject } from "react-router";

import ProtectedRoute from "~/components/ProtectedRoute";
import {
  BookingsRoute,
  UnverifiedBookingsRoute,
  VerifiedBookingsRoute,
} from "~/features/financial-admin";
import { RevenuePage, RevenueRoute } from "~/features/financial-admin/revenue";
import { SEAPage, SEARoute } from "~/features/financial-admin/sea";

export const financialAdminRoutes: RouteObject = {
  path: "financial-admin",
  element: <ProtectedRoute allowedRoles={["isFinancialAdmin"]} />,
  children: [
    { index: true, element: <Navigate to="bookings" replace /> },
    {
      path: "bookings",
      element: <BookingsRoute />,
      children: [
        { index: true, element: <Navigate to="unverified" replace /> },
        {
          path: "unverified",
          element: <UnverifiedBookingsRoute />,
        },
        {
          path: "verified",
          element: <VerifiedBookingsRoute />,
        },
      ],
    },
    {
      path: "revenue",
      element: <RevenueRoute />,
      children: [
        { index: true, element: <Navigate to="htec" replace /> },
        { path: "htec", element: <RevenuePage /> },
        { path: "cxea", element: <RevenuePage /> },
        { path: "cogs", element: <RevenuePage /> },
      ],
    },
    {
      path: "SEA",
      element: <SEARoute />,
      children: [
        { index: true, element: <Navigate to="sea" replace /> },
        { path: "sea", element: <SEAPage /> },
      ],
    },
  ],
};
