import { getCanvasTasks, getEngagementTasks } from "~/api/thought-spot";
import {
  canvasTasksQueryKeyList,
  engagementTasksQueryKeys,
} from "~/utils/queryKeys";

export const thoughtSpotCanvasTasksQuery = ({
  canvasId,
  engagementId,
}: {
  canvasId: number;
  engagementId: number;
}) => ({
  queryKey: canvasTasksQueryKeyList(canvasId, engagementId),
  queryFn: () => getCanvasTasks(canvasId),
});

export const thoughtSpotEngagementTasksQuery = (engagementId: number) => ({
  queryKey: engagementTasksQueryKeys.list(engagementId),
  queryFn: () => getEngagementTasks(engagementId),
});
