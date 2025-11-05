import client, { V2_URL } from "~/app/api";
import {
  ITmlPayload,
  ITmlResponse,
  TFetchTmlProps,
  TmlResponseSchema,
} from "~/domain/Tml";

export const getTml = async (payload: TFetchTmlProps) => {
  const response = await client.get<ITmlResponse>(
    `${V2_URL}/file_management/file_management_json/get_state?dc_engagement_id=${payload.dc_engagement_id}&canvas_id=${payload.canvas_id}`,
  );
  return TmlResponseSchema.parse(response.data);
};

export const createTml = async (payload: {
  engagementId: number;
  canvasId: number;
  tml: ITmlPayload;
  defer: boolean;
}) => {
  const response = await client.post<ITmlResponse>(
    `${V2_URL}/file_management/file_management_json/post_state?dc_engagement_id=${payload.engagementId}&canvas_id=${payload.canvasId}&defer=${payload.defer}`,
    payload.tml,
  );
  return response.data;
};
