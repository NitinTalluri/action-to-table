import { Navigate, RouteObject } from "react-router";

import BookingContracts from "~/features/contract/tabs/bookings/BookingContracts";
import ContractTabs from "~/features/contract/tabs/ContractTabs";
import MonitoredContracts from "~/features/contract/tabs/monitored/MonitoredContracts";
import { EngagementRoute } from "~/features/engagements/EngagementRoute";
import { EngagementsTableRoute } from "~/features/engagements/EngagementsTableRoute";
import {
  CanvasesRoute,
  DeliverablesRoute,
  LinksRoute,
  StakeholdersRoute,
  TagsetRoute,
} from "~/features/engagements/sub-routes";

export const engagementsRoutes: RouteObject = {
  path: "engagements",
  children: [
    {
      index: true,
      element: <EngagementsTableRoute />,
    },
    {
      path: ":engagementId",
      element: <EngagementRoute />,
      children: [
        {
          index: true,
          element: <Navigate to={"canvases"} replace />,
        },
        {
          path: "canvases",
          element: <CanvasesRoute />,
        },
        {
          path: "stakeholders",
          element: <StakeholdersRoute />,
        },
        {
          path: "contracts",
          element: <ContractTabs />,
          children: [
            {
              index: true,
              element: <BookingContracts />,
            },
            {
              path: "monitored",
              element: <MonitoredContracts />,
            },
          ],
        },
        {
          path: "links",
          element: <LinksRoute />,
        },
        {
          path: "tagsets",
          element: <TagsetRoute />,
        },
        {
          path: "deliverables",
          element: <DeliverablesRoute />,
        },
      ],
    },
  ],
};
