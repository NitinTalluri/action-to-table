import { redirect, RouteObject } from "react-router";

import { WorkflowUiEnum } from "~/domain/Workflows";
import {
  WorkflowEventDetailRoute,
  WorkflowEventsListRoute,
  WorkflowEventsRoute,
} from "~/features/workflow-events";
import { LogSignOffRoute } from "~/features/workflows/account-management";
import { GenerateDocusignScopeRoute } from "~/features/workflows/account-management/generate-docusign-scope/GenerateDocusignScopeRoute";
import { ACATDiscoveryRoute } from "~/features/workflows/look-ups/acat-discovery";
import { HostnameRelinkRoute } from "~/features/workflows/look-ups/hostname-relink";
import { HostnameSiteMovesRoute } from "~/features/workflows/look-ups/hostname-site-moves";
import { SiteReportRoute } from "~/features/workflows/look-ups/site-report";
import SNIFReportRoute from "~/features/workflows/look-ups/snif-report";
import { TagHistoryRoute } from "~/features/workflows/look-ups/tag-history/TagHistoryRoute";
import AddToContractRoute from "~/features/workflows/MACD/add-to-contract";
import MACDAuditRoute from "~/features/workflows/MACD/macd-audit/MACDAuditRoute";
import MACDUploadAddRoute from "~/features/workflows/MACD/macd-upload/add/MACDUploadAddRoute";
import { MACDUploadHistoricalRoute } from "~/features/workflows/MACD/macd-upload/historical/MACDUploadHistoricalRoute";
import MACDUploadRoute from "~/features/workflows/MACD/macd-upload/MACDUploadRoute";
import BulkTaggingRoute from "~/features/workflows/tagging/bulk-tagging/BulkTaggingRoute";
import InstanceTaggingRoute from "~/features/workflows/tagging/instance-tagging/InstanceTaggingRoute";
import SerialTaggingRoute from "~/features/workflows/tagging/serial-tagging/SerialTaggingRoute";
import CollectorFileRoute from "~/features/workflows/uploads/collector-file/CollectorFileRoute";
import CustomerFileRoute from "~/features/workflows/uploads/customer-file/CustomerFileRoute";
import SeaFileRoute from "~/features/workflows/uploads/sea/SeaFileRoute";
import { Workflow404 } from "~/features/workflows/Workflow404";
import WorkflowPage from "~/features/workflows/WorkflowPage";
import { ClearSearchBoundary } from "~/router/ClearSearchBoundary";

export const workflowRoutes: RouteObject = {
  path: "/workflows/:engagementId",
  element: <WorkflowPage />,
  children: [
    {
      path: WorkflowUiEnum.Enum["log-signoff"],
      element: <LogSignOffRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["generate-docusign-scope"],
      element: <GenerateDocusignScopeRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["instance-tagging"],
      element: <InstanceTaggingRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["serial-tagging"],
      element: <SerialTaggingRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["bulk-tagging"],
      element: <BulkTaggingRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["site-report"],
      element: <SiteReportRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["acat-discovery"],
      element: <ACATDiscoveryRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["host-name-relink"],
      element: <HostnameRelinkRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["host-name-site-moves"],
      element: <HostnameSiteMovesRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["snif-report"],
      element: <SNIFReportRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["tag-history"],
      element: <TagHistoryRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["add-to-contract"],
      element: <AddToContractRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["customer-upload"],
      element: <CustomerFileRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["collector-upload"],
      element: <CollectorFileRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["sea-upload"],
      element: <SeaFileRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["macd-upload"],
      children: [
        {
          index: true,
          element: <MACDUploadRoute />,
        },
        {
          path: "add",
          element: <MACDUploadAddRoute />,
        },
      ],
    },
    {
      path: WorkflowUiEnum.Enum["macd-historical-upload"],
      element: <MACDUploadHistoricalRoute />,
      errorElement: <ClearSearchBoundary />,
    },
    {
      path: WorkflowUiEnum.Enum["macd-audit"],
      element: <MACDAuditRoute />,
    },
    {
      path: WorkflowUiEnum.Enum["canvas-actions"],
      // redirecting to workflow's notifications because this workflow is only a stream of notifications
      loader: ({ request }) => {
        const urlSearchParams = new URL(request.url).searchParams;

        return redirect(
          `../events/${WorkflowUiEnum.Enum["canvas-actions"]}?${urlSearchParams.toString()}`,
        );
      },
    },
    {
      path: WorkflowUiEnum.Enum["general-notification"],
      // redirecting to workflow's notifications because this workflow is only a stream of notifications
      loader: ({ request }) => {
        const urlSearchParams = new URL(request.url).searchParams;

        redirect(
          `../events/${WorkflowUiEnum.Enum["general-notification"]}?${urlSearchParams.toString()}`,
        );
      },
    },
    {
      path: "events/:eventUiEnum",
      element: <WorkflowEventsRoute />,
      children: [
        {
          index: true,
          element: <WorkflowEventsListRoute />,
        },
        {
          path: ":notificationId/*",
          element: <WorkflowEventDetailRoute />,
        },
      ],
    },
    {
      path: "*",
      element: <Workflow404 />,
    },
  ],
};
