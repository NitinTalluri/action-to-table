import { getFileManagement } from "~/api/file-management";
import { fileManagementQueryKeys } from "~/utils/queryKeys";

export const fileManagementQuery = (request: {
  engagementId: number;
  canvasId: number;
}) => ({
  queryKey: fileManagementQueryKeys.list(request),
  queryFn: () => getFileManagement(request),
});
