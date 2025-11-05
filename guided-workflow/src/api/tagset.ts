import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  DeletedTagsetResponseSchema,
  TagsetEngagementSchema,
  TagSetGlobalResponseSchema,
  TagsetGlobalSchema,
  TagSetResponseSchema,
  TDeletedTagsetResponse,
  TTagsetEngagement,
  TTagsetGlobal,
  TTagsetGlobalRequest,
  TTagsetRequest,
} from "~/domain/Tagset";

export const getTagsets = async (engagementId: number) => {
  const response = await client.get(`${V2_URL}/tagsets/${engagementId}`);
  return z.array(TagsetEngagementSchema).parse(response.data);
};

export const getDeletedTagsets = async (): Promise<
  TDeletedTagsetResponse[]
> => {
  const response = await client.get(`${V2_URL}/tagsets/1/deleted`);
  return DeletedTagsetResponseSchema.array().parse(response.data);
};

export const getGlobalTagsets = async () => {
  const response = await client.get(`${V2_URL}/tagsets/1/global`);
  return z.array(TagsetGlobalSchema).parse(response.data);
};

export const updateTagset = async (tagsetData: TTagsetEngagement) => {
  const response = await client.patch(
    `${V2_URL}/tagsets/${tagsetData.dc_engagement_id}/${tagsetData.tagset_id}`,
    tagsetData,
  );
  return TagSetResponseSchema.parse(response.data);
};

export const updateGlobalTagset = async (tagsetData: TTagsetGlobal) => {
  const response = await client.patch(
    `${V2_URL}/tagsets/1/global/${tagsetData.tagset_id}`,
    tagsetData,
  );
  return TagSetResponseSchema.parse(response.data);
};

export const createTagset = async (tagsetData: TTagsetRequest) => {
  const response = await client.post(
    `${V2_URL}/tagsets/${tagsetData.dc_engagement_id}`,
    tagsetData,
  );
  return TagSetResponseSchema.parse(response.data);
};

export const createGlobalTagset = async (tagsetData: TTagsetGlobalRequest) => {
  const response = await client.post(`${V2_URL}/tagsets/1/global`, tagsetData);
  return TagSetGlobalResponseSchema.parse(response.data);
};

export const undeleteTagset = async (tagsetId: number) => {
  const response = await client.put(`${V2_URL}/tagsets/1/undelete/${tagsetId}`);
  return TagSetResponseSchema.parse(response.data);
};

export const extractTagsets = async (engagementId: number) => {
  const response = await client.get(
    `${V2_URL}/tagsets/extract/${engagementId}`,
    { responseType: "blob" },
  );

  const blob = new Blob([response.data], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  return blob;
};
