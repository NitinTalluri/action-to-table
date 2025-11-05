import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  DeletedEngagementSchema,
  EngagementOwnersResponseSchema,
  TDeletedEngagement,
  TEngagement,
} from "~/domain/Engagement";
import { UserSchema } from "~/domain/Users";
import { returnParsedArrayData } from "~/utils/safeParse";

export const getEngagementsUsers = async () => {
  const response = await client.get(`${V2_URL}/engagements/users`);
  return returnParsedArrayData(response.data, z.array(UserSchema));
};

export const getEngagements = async () => {
  const response = await client.get<TEngagement[]>(`${V2_URL}/engagements`);
  return response.data;
};

export const getDeletedEngagements = async () => {
  const response = await client.get<TDeletedEngagement[]>(
    `${V2_URL}/engagements/deleted`,
  );
  return returnParsedArrayData(response.data, DeletedEngagementSchema.array());
};

export const undeleteEngagement = async (dc_engagement_id: number) => {
  const response = await client.put(
    `${V2_URL}/engagements/${dc_engagement_id}`,
  );
  return response.data;
};

export const createEngagement = async (engagement: TEngagement) => {
  const response = await client.post<TEngagement>(
    `${V2_URL}/engagements`,
    engagement,
  );
  return response.data;
};

export const updateEngagement = async (engagement: Partial<TEngagement>) => {
  const response = await client.patch<TEngagement>(
    `${V2_URL}/engagements/${engagement.dc_engagement_id}`,
    engagement,
  );
  return response.data;
};

export const deleteEngagement = async (dc_engagement_id: number) => {
  const response = await client.delete<TEngagement>(
    `${V2_URL}/engagements/${dc_engagement_id}`,
  );
  return response.data;
};

export const getEngagementOwners = async (dc_engagement_id: number) => {
  const response = await client.get(
    `${V2_URL}/engagements/engagement_owners/${dc_engagement_id}`,
  );
  return returnParsedArrayData(response.data, EngagementOwnersResponseSchema);
};

export const createEngagementOwner = async ({
  dc_engagement_id,
  cco_id,
}: {
  dc_engagement_id: number;
  cco_id: string;
}) => {
  const response = await client.post(
    `${V2_URL}/engagements/${dc_engagement_id}/share/${cco_id}`,
  );
  return response.data;
};

export const deleteEngagementOwner = async ({
  dc_engagement_id,
  cco_id,
}: {
  dc_engagement_id: number;
  cco_id: string;
}) => {
  const response = await client.delete(
    `${V2_URL}/engagements/${dc_engagement_id}/share/${cco_id}`,
  );
  return response.data;
};

export const createEngagementOwnerAsAdmin = async ({
  dc_engagement_id,
  cco_id,
  logged_user,
}: {
  dc_engagement_id: number;
  cco_id: string;
  logged_user: string;
}) => {
  const response = await client.post(
    `${V2_URL}/engagements/${dc_engagement_id}/share/${cco_id}?logged_user=${logged_user}`,
  );
  return response.data;
};
