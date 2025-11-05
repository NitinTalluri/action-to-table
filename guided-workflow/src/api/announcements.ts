import client, { V2_URL } from "~/app/api";
import {
  AnnouncementSchema,
  TAnnouncement,
  TAnnouncementRequest,
} from "~/domain/Announcements";
import { returnParsedArrayData, returnParsedData } from "~/utils/safeParse";

export const getAnnouncements = async (
  dashboard_view: boolean,
): Promise<TAnnouncement[]> => {
  const response = await client.get(`${V2_URL}/announcements`, {
    params: { dashboard_view },
  });
  return returnParsedArrayData(response.data, AnnouncementSchema.array());
};

export const getAnnouncement = async (id: number) => {
  const response = await client.get(`${V2_URL}/announcements/${id}`);
  return returnParsedData(response.data, AnnouncementSchema);
};

export const createAnnouncement = async (data: TAnnouncementRequest) => {
  const response = await client.post(`${V2_URL}/announcements`, data);
  return returnParsedData(response.data, AnnouncementSchema);
};

export const updateAnnouncement = async ({
  id,
  data,
}: {
  id: number;
  data: TAnnouncementRequest;
}) => {
  const response = await client.put(`${V2_URL}/announcements/${id}`, data);
  return returnParsedData(response.data, AnnouncementSchema);
};

export const deleteAnnouncement = async (id: number) => {
  const response = await client.delete(`${V2_URL}/announcements/${id}`);
  return response.data;
};

export const dismissAnnouncement = async ({
  id,
  is_dismissed,
}: {
  id: number;
  is_dismissed: boolean;
}) => {
  const response = await client.put(`${V2_URL}/announcements/${id}/status`, {
    is_dismissed,
  });
  return returnParsedData(response.data, AnnouncementSchema);
};
