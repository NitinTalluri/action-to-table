import client, { V2_URL } from "~/app/api";
import { ArchivedLiveboardsResponseSchema } from "~/domain/file-management";

export const getFileManagement = async (request: {
  engagementId: number;
  canvasId: number;
}) => {
  const response = await client.get(
    `${V2_URL}/file_management/archived/${request.engagementId}/${request.canvasId}`,
  );
  return ArchivedLiveboardsResponseSchema.parse(response.data);
};
