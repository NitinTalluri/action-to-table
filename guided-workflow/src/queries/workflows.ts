import {
  getWorkflowNotification,
  getWorkflowNotifications,
} from "~/api/workflows";
import { workflowNotificationsQueryKeys } from "~/utils/queryKeys";

export const getEngagementNotificationsQuery = (engagementId: number) => ({
  queryKey: workflowNotificationsQueryKeys.list(engagementId),
  queryFn: () => getWorkflowNotifications(engagementId),
});

export const getEngagementNotificationQuery = ({
  engagementId,
  notificationId,
}: {
  engagementId: number;
  notificationId: number;
}) => ({
  queryKey: workflowNotificationsQueryKeys.detail(engagementId, notificationId),
  queryFn: () => getWorkflowNotification(engagementId, notificationId),
});
