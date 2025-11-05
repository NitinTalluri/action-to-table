import {
  fetchDeliverable,
  fetchSdpData,
  fetchSubtask,
  fetchTask,
} from "~/api/sdp";
import { sdpQueryKeys } from "~/utils/queryKeys";

export const sdpDeliverableQueryKey = (id: number) =>
  sdpQueryKeys.detail(["deliverable", id]);
export const sdpSubtaskQueryKey = (id: number) =>
  sdpQueryKeys.detail(["subtask", id]);
export const sdpTaskQueryKey = (id: number) =>
  sdpQueryKeys.detail(["task", id]);

export const getSdpDataQuery = {
  queryKey: sdpQueryKeys.lists(),
  queryFn: fetchSdpData,
  // staletime of 5 minutes
  staleTime: 1000 * 60 * 5,
};

export const getDeliverableQuery = (id: number | string) => {
  return {
    queryKey: sdpDeliverableQueryKey(Number(id)),
    queryFn: () => fetchDeliverable(Number(id)),
  };
};

export const getSubtaskQuery = ({ id }: { id: number | string }) => {
  return {
    queryKey: sdpSubtaskQueryKey(Number(id)),
    queryFn: () => fetchSubtask(Number(id)),
  };
};

export const getTaskQuery = (id: number | string) => {
  return {
    queryKey: sdpTaskQueryKey(Number(id)),
    queryFn: () => fetchTask(Number(id)),
  };
};
