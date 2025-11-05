import { Box } from "@mui/material";
import { createBrowserRouter, redirect } from "react-router";

import LoadingSpinnerFullPage from "~/components/Loading/LoadingSpinnerFullPage";
import { NotFound } from "~/components/not-found";
import { SchemaResultDevPage } from "~/dev/SchemaResultDevPage";
import TimeTrackingRoute from "~/features/time-tracking/time-tracking-route";
import { RootRoute } from "~/RootRoute";

import { adminRoutes } from "./admin-routes";
import { engagementsRoutes } from "./engagements-routes";
import { financialAdminRoutes } from "./financial-admin-routes";
import { managerPortalRoutes } from "./manager-portal-routes";
import { supportRoutes } from "./support-routes";
import { workflowRoutes } from "./workflow-routes";

export const router = () =>
  createBrowserRouter([
    {
      element: <RootRoute />,
      hydrateFallbackElement: <LoadingSpinnerFullPage />,
      children: [
        {
          path: "/",
          loader: () => redirect("engagements"),
        },
        engagementsRoutes,
        workflowRoutes,
        {
          path: "time-tracking",
          element: <TimeTrackingRoute />,
        },
        {
          path: "dev/schema-result",
          element: <SchemaResultDevPage />,  // TODO - Remove before deploy
        },
        financialAdminRoutes,
        adminRoutes,
        managerPortalRoutes,
        supportRoutes,
        {
          path: "*",
          element: (
            <Box sx={{ height: "100vh" }}>
              <NotFound />
            </Box>
          ),
        },
      ],
    },
  ]);
