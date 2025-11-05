import client, { V2_URL } from "~/app/api";
import {
  DeliverableApiSchema,
  SdpApiSchema,
  SubtaskApiSchema,
  TaskApiSchema,
  TDeliverable,
  TSdpData,
  TSubtask,
  TTask,
} from "~/domain/SDP";

export const fetchSdpData = async (): Promise<TSdpData> => {
  const endpoint = "/api/v2/admin/sdp";
  const response = await client.get(endpoint);
  return SdpApiSchema.parse(response.data);
};

export const fetchSubtask = async (id: number): Promise<TSubtask> => {
  const endpoint = `/api/v2/admin/sdp/subtasks/${id}`;
  const response = await client.get(endpoint);
  return SubtaskApiSchema.parse(response.data);
};

export const updateSubtask = async ({
  id,
  updatedSubtask,
}: {
  id: number;
  updatedSubtask: TSubtask;
}): Promise<TSubtask> => {
  const response = await client.patch(
    `/api/v2/admin/sdp/subtasks/${id}`,
    updatedSubtask,
  );
  return SubtaskApiSchema.parse(response.data);
};

export const createSubtask = async (
  updatedSubtask: TSubtask,
): Promise<TSubtask> => {
  const response = await client.post(
    `/api/v2/admin/sdp/subtasks`,
    updatedSubtask,
  );
  return SubtaskApiSchema.parse(response.data);
};

export const deleteSubtask = async (id: number) => {
  return await client.delete(`/api/v2/admin/sdp/subtasks/${id}`);
};

export const fetchTask = async (id: number): Promise<TTask> => {
  const response = await client.get(`/api/v2/admin/sdp/tasks/${id}`);
  return TaskApiSchema.parse(response.data);
};

export const updateTask = async ({
  id,
  updatedTask,
}: {
  id: number;
  updatedTask: TTask;
}): Promise<TTask> => {
  const response = await client.patch(
    `/api/v2/admin/sdp/tasks/${id}`,
    updatedTask,
  );
  return TaskApiSchema.parse(response.data);
};

export const createTask = async (updatedTask: TTask): Promise<TTask> => {
  const response = await client.post(`/api/v2/admin/sdp/tasks`, updatedTask);
  return TaskApiSchema.parse(response.data);
};

export const deleteTask = async (id: number) => {
  return await client.delete(`/api/v2/admin/sdp/tasks/${id}`);
};

export const fetchDeliverable = async (id: number): Promise<TDeliverable> => {
  const response = await client.get(`/api/v2/admin/sdp/deliverables/${id}`);
  return DeliverableApiSchema.parse(response.data);
};

export const updateDeliverable = async ({
  id,
  updatedDeliverable,
}: {
  id: number;
  updatedDeliverable: TDeliverable;
}): Promise<TDeliverable> => {
  const response = await client.patch(
    `/api/v2/admin/sdp/deliverables/${id}`,
    updatedDeliverable,
  );
  return DeliverableApiSchema.parse(response.data);
};

export const createDeliverable = async (
  updatedDeliverable: TDeliverable,
): Promise<TDeliverable> => {
  const response = await client.post(
    `/api/v2/admin/sdp/deliverables`,
    updatedDeliverable,
  );
  return DeliverableApiSchema.parse(response.data);
};

export const deleteDeliverable = async (id: number) => {
  return await client.delete(`/api/v2/admin/sdp/deliverables/${id}`);
};

export const rebuildSDP = async () => {
  return await client.post(`${V2_URL}/admin/sdp/rebuild`);
};
