import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  DeletedTagSchema,
  TagSchema,
  TDeletedTag,
  TTag,
  TTagRequest,
} from "~/domain/Tags";

export const getTags = async (engagementId: number) => {
  const response = await client.get(`${V2_URL}/tags/${engagementId}`);
  return z.array(TagSchema).parse(response.data);
};

export const getDeletedTags = async (): Promise<TDeletedTag[]> => {
  const response = await client.get(`${V2_URL}/tags/1/deleted`);
  return z.array(DeletedTagSchema).parse(response.data);
};

export const undeleteTag = async (tagId: number) => {
  const response = await client.put(`${V2_URL}/tags/1/undelete/${tagId}`);
  return response.data;
};

export const createTag = async ({
  tagData,
  engagementId,
}: {
  tagData: TTagRequest;
  engagementId: number;
}) => {
  const response = await client.post(`${V2_URL}/tags/${engagementId}`, tagData);
  return TagSchema.parse(response.data);
};

export const createTags = async ({
  tags,
  engagementId,
}: {
  tags: TTagRequest[];
  engagementId: number;
}) => {
  const reponses = tags.map(async (tag) => {
    const response = await client.post(`${V2_URL}/tags/${engagementId}`, tag);
    return TagSchema.parse(response.data);
  });
  return Promise.all(reponses);
};

export const deleteTag = async (tagId: number) => {
  const response = await client.delete(`${V2_URL}/tags/${tagId}`);
  return TagSchema.parse(response.data);
};

export const deleteTags = async (tagIds: number[]) => {
  const reponses = tagIds.map(async (tagId) => {
    const response = await client.delete(`${V2_URL}/tags/${tagId}`);
    return TagSchema.parse(response.data);
  });
  return Promise.all(reponses);
};

export const createGlobalTag = async (tagData: TTagRequest) => {
  const response = await client.post(`${V2_URL}/tags/1/global`, tagData);
  return TagSchema.parse(response.data);
};

export const createGlobalTags = async (tags: TTagRequest[]) => {
  const reponses = tags.map(async (tag) => {
    const response = await client.post(`${V2_URL}/tags/1/global`, tag);
    return TagSchema.parse(response.data);
  });
  return Promise.all(reponses);
};

export const deleteGlobalTag = async (tagId: number) => {
  const response = await client.delete(`${V2_URL}/tags/1/global/${tagId}`);
  return TagSchema.parse(response.data);
};

export const deleteGlobalTags = async (tagIds: number[]) => {
  const reponses = tagIds.map(async (tagId) => {
    const response = await client.delete(`${V2_URL}/tags/1/global/${tagId}`);
    return TagSchema.parse(response.data);
  });
  return Promise.all(reponses);
};

export const updateTag = async ({
  tagData,
  engagementId,
}: {
  tagData: TTag;
  engagementId: number;
}) => {
  const response = await client.patch(
    `${V2_URL}/tags/${engagementId}/${tagData.tag_id}`,
    tagData,
  );
  return TagSchema.parse(response.data);
};

export const updateGlobalTag = async (tagData: TTag) => {
  const response = await client.patch(
    `${V2_URL}/tags/1/global/${tagData.tag_id}`,
    tagData,
  );
  return TagSchema.parse(response.data);
};
