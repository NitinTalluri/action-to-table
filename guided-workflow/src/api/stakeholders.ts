import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  IStakeholder,
  IStakeholderCreate,
  StakeholderSchema,
} from "~/domain/Stakeholder";

export const getStakeholders = async (engagementId: number) => {
  const response = await client.get(`${V2_URL}/stakeholders/${engagementId}`);
  return z.array(StakeholderSchema).parse(response.data);
};

export const deleteStakeholder = async ({
  engagementId,
  stakeholderId,
}: {
  engagementId: number;
  stakeholderId: number;
}) => {
  const response = await client.delete(
    `${V2_URL}/stakeholders/${engagementId}/${stakeholderId}`,
  );
  return StakeholderSchema.parse(response.data);
};

export const createStakeholder = async (stakeholder: IStakeholderCreate) => {
  const response = await client.post(
    `${V2_URL}/stakeholders/${stakeholder.dc_engagement_id}`,
    stakeholder,
  );
  return StakeholderSchema.parse(response.data);
};

export const editStakeholder = async (stakeholder: IStakeholder) => {
  const response = await client.patch(
    `${V2_URL}/stakeholders/${stakeholder.dc_engagement_id}/${stakeholder.stakeholder_id}`,
    stakeholder,
  );
  return StakeholderSchema.parse(response.data);
};
