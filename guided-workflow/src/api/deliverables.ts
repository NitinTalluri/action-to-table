import client, { V2_URL } from "~/app/api";
import {
  ActiveDeliverablesResponseSchema,
  ClosedDeliverablesResponseSchema,
  DeliverablesResponseSchema,
  ScheduledDeliverablesResponseSchema,
  TUpdateTaskStatus,
  UpdateTaskStatusResponseSchema,
} from "~/domain/Deliverables";

export const getDeliverables = async (engagementID: number) => {
  const response = await client.get(
    `${V2_URL}/sdp/${engagementID}/deliverables`,
  );
  return DeliverablesResponseSchema.parse(response.data);
};

export const getScheduledDeliverables = async (engagementID: number) => {
  const response = await client.get(
    `${V2_URL}/sdp/${engagementID}/deliverables/scheduled`,
  );
  return ScheduledDeliverablesResponseSchema.parse(response.data);
};

export const getClosedDeliverables = async (engagementID: number) => {
  const response = await client.get(
    `${V2_URL}/sdp/${engagementID}/deliverables/closed`,
  );
  return ClosedDeliverablesResponseSchema.parse(response.data);
};

export const getActiveDeliverables = async (engagementID: number) => {
  const response = await client.get(
    `${V2_URL}/sdp/${engagementID}/deliverables/active`,
  );
  return ActiveDeliverablesResponseSchema.parse(response.data);
};

export const updateTaskStatus = async (updateTask: TUpdateTaskStatus) => {
  const response = await client.put(`${V2_URL}/sdp/completions`, updateTask);

  return UpdateTaskStatusResponseSchema.parse(response.data);
};
