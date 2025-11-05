import {
  getCanvases,
  getCustomerCollectorFiles,
  getDeletedCanvases,
  getSnapshotDates,
} from "~/api/canvases";
import {
  canvasesQueryKeys,
  canvasEvidenceFilesQueryKeys,
} from "~/utils/queryKeys";

export const canvasesQuery = (engagementId: number) => ({
  queryKey: canvasesQueryKeys.list(engagementId),
  queryFn: () => getCanvases(engagementId),
});

export const deletedCanvasesQuery = {
  queryKey: canvasesQueryKeys.list("deleted"),
  queryFn: getDeletedCanvases,
};

export const canvasCustomerCollectorFiles = (engagementId: number) => ({
  queryKey: canvasEvidenceFilesQueryKeys.list(engagementId),
  queryFn: () => getCustomerCollectorFiles(engagementId),
});

export const canvasSnapshotDates = () => ({
  queryKey: canvasEvidenceFilesQueryKeys.list(),
  queryFn: () => getSnapshotDates(),
});
