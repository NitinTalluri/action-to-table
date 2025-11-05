import client, { V2_URL } from "~/app/api";
import { tsClient } from "~/app/thoughtspotApi";
import { TEngagementTaskSubmission } from "~/domain/EngagementTasks";
import { EngagementTaskSchemaArray } from "~/domain/EngagementTasksAPI";
import {
  TCreateTagActionsPayload,
  TSendExtractInstanceIds,
} from "~/domain/thoughtspot";
import { returnParsedArrayData } from "~/utils/safeParse";

type TStartThoughtSpotParams = {
  dc_engagement_id: number;
  canvas_id: number;
};

type TStartThoughtSpotResponse = {
  request_id: number;
  success: boolean;
  message: string;
};

export const startThoughtSpotDiscovery = async (
  params: TStartThoughtSpotParams,
) => {
  const response = await client.post<TStartThoughtSpotResponse>(
    `${V2_URL}/thought_spot/discover`,
    params,
  );
  const parsed = response.data;
  if (!parsed.success) {
    throw new Error(parsed.message);
  }
  return parsed;
};

export const getCanvasTasks = async (canvasId: number) => {
  const response = await client.get(
    `${V2_URL}/thought_spot/canvas_tasks/${canvasId}`,
  );
  return returnParsedArrayData(response.data, EngagementTaskSchemaArray);
};

export const getEngagementTasks = async (engagementId: number) => {
  const response = await client.get(`${V2_URL}/thought_spot/${engagementId}`);
  return returnParsedArrayData(response.data, EngagementTaskSchemaArray);
};

export const deleteTagActions = async (thoughtspot_ids: number[]) => {
  const response = await client.delete(`${V2_URL}/thought_spot`, {
    data: { thoughtspot_ids },
  });
  return response.data;
};

export const createTagActions = async ({
  requests,
}: TCreateTagActionsPayload) => {
  const response = await client.post(`${V2_URL}/thought_spot_tag`, {
    requests,
  });
  return response.data;
};

export const sendExtractInstanceIds = async ({
  columnsToExtract,
  engagementId,
  idList,
}: TSendExtractInstanceIds) => {
  const response = await client.post(
    `${V2_URL}/thought_spot/actions/extracts`,
    {
      idList,
      columnsToExtract,
      engagementId,
    },
  );
  return response.data;
};

export const uploadModalSubmission = async (
  payload: TEngagementTaskSubmission,
) => {
  const {
    context: { answerUrl },
    canvas_id,
    comment,
    engagement_id,
    tag_ids,
    tagset_ids,
    user_action,
    context,
    config_strategy,
  } = payload;

  const rawResponse = await tsClient.get<Blob>(answerUrl, {
    responseType: "blob",
  });
  const blob = rawResponse.data;

  const formData = new FormData();
  const fileName = "records.csv";

  const modalParams = {
    canvas_id,
    comment,
    engagement_id,
    tag_ids,
    tagset_ids,
    user_action,
    context,
    config_strategy,
  };

  formData.append("records", blob, fileName);
  formData.append("data", JSON.stringify(modalParams));

  const response = await client.post(
    `${V2_URL}/thought_spot/upload/${engagement_id}`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );

  return response.data;
};

export const refreshTagsets = async (payload: TStartThoughtSpotParams) => {
  const response = await client.post(
    `${V2_URL}/thought_spot/refresh-tagsets`,
    payload,
  );
  return response.data;
};
