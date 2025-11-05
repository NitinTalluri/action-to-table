import client, { V2_URL } from "~/app/api";
import {
  CaseListAgentItemResponseSchema,
  CaseListItemResponseSchema,
  CaseResponseBodySchema,
  SprintGoalsResponseSchema,
  TCaseListAgentFilters,
  TCaseListAgentItemResponse,
  TCaseListItemResponse,
  TCaseRequestBody,
  TSprintGoalsResponse,
} from "~/domain/Support";
import { IUser, UserSchema } from "~/domain/Users";

export const postSupportCases = async (data: TCaseRequestBody) => {
  const response = await client.post(`${V2_URL}/support/cases`, data);
  return CaseResponseBodySchema.parse(response.data);
};

export const getSupportCases = async (): Promise<TCaseListItemResponse[]> => {
  const response = await client.get(`${V2_URL}/support/cases`);
  return CaseListItemResponseSchema.array().parse(response.data);
};

export const getSupportAgentCases = async (
  filters: Partial<TCaseListAgentFilters>,
): Promise<TCaseListAgentItemResponse[]> => {
  const response = await client.get(`${V2_URL}/support/agent`, {
    params: filters,
  });
  return CaseListAgentItemResponseSchema.array().parse(response.data);
};

export const getSupportAgentCase = async (
  caseId: number,
): Promise<TCaseListAgentItemResponse> => {
  const response = await client.get(`${V2_URL}/support/agent/${caseId}`);
  return CaseListAgentItemResponseSchema.parse(response.data);
};

export const getSupportAvailableAgents = async (): Promise<IUser[]> => {
  const response = await client.get(`${V2_URL}/support/agent/available_agents`);
  return UserSchema.array().parse(response.data);
};

export const putSupportAgentCase = async (
  c: Partial<TCaseListAgentItemResponse> & { is_resolved?: boolean },
) => {
  const response = await client.put(`${V2_URL}/support/agent/${c.case_id}`, c);
  return CaseListAgentItemResponseSchema.parse(response.data);
};

export const postSupportCloseCase = async (
  caseId: number,
): Promise<TCaseListItemResponse> => {
  const response = await client.post(
    `${V2_URL}/support/cases/${caseId}/close`,
    { comments: "" },
  );
  return CaseListItemResponseSchema.parse(response.data);
};

export const getSprintGoals = async (): Promise<TSprintGoalsResponse> => {
  const response = await client.get(`${V2_URL}/static/html`);
  return SprintGoalsResponseSchema.parse(response.data);
};
