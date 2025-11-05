import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  CanvasItem,
  CanvasResponseSchema,
  CustomerCollectorFileSchema,
  DeletedCanvasSchema,
  SnapshotDatesSchema,
  TCreateCanvasParams,
  TDeletedCanvas,
  TRefreshCanvasParams,
} from "~/domain/Canvas";

export const getCanvases = async (engagementId: number) => {
  const response = await client.get(`${V2_URL}/canvas/${engagementId}`);
  return CanvasResponseSchema.parse(response.data);
};

export const getDeletedCanvases = async (): Promise<TDeletedCanvas[]> => {
  const response = await client.get(`${V2_URL}/canvas/1/deleted`);
  return DeletedCanvasSchema.array().parse(response.data);
};

export const undeleteCanvas = async (canvasId: number) => {
  const response = await client.put(`${V2_URL}/canvas/1/undelete/${canvasId}`);
  return DeletedCanvasSchema.parse(response.data);
};

export const createCanvas = async (data: TCreateCanvasParams) => {
  const response = await client.post(`${V2_URL}/canvas`, data);
  return CanvasItem.parse(response.data);
};

export const refreshCanvas = async (data: TRefreshCanvasParams) => {
  const response = await client.post(`${V2_URL}/canvas/rebuild`, data);
  return CanvasItem.parse(response.data);
};

export const deleteCanvas = async ({
  engagementId,
  canvasId,
}: {
  engagementId: number;
  canvasId: number;
}) => {
  const response = await client.delete(
    `${V2_URL}/canvas/${engagementId}/canvas/${canvasId}`,
  );
  return CanvasItem.parse(response.data);
};

export const getCustomerCollectorFiles = async (engagementId: number) => {
  const response = await client.get(
    `${V2_URL}/canvas/${engagementId}/evidence_uploads`,
  );
  return z.array(CustomerCollectorFileSchema).parse(response.data);
};

export const getSnapshotDates = async () => {
  const response = await client.get(`${V2_URL}/canvas/snapshots`);
  return z.array(SnapshotDatesSchema).parse(response.data);
};
