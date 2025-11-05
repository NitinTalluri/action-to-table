import client, { V2_URL } from "~/app/api";
import { EngagementLinksSchema, LinkSchema, TLink } from "~/domain/Engagement";

export const getEngagementLinks = async (engagementId: number) => {
  const response = await client.get(`${V2_URL}/links/${engagementId}`);
  return EngagementLinksSchema.parse(response.data);
};

export const deleteEngagementLink = async (link: TLink) => {
  const response = await client.delete(
    `${V2_URL}/links/${link.dc_engagement_id}/${link.link_type}/${link.id}`,
  );
  return LinkSchema.parse(response.data);
};

export const createEngagementLink = async (link: TLink) => {
  const response = await client.post(
    `${V2_URL}/links/${link.dc_engagement_id}/${link.link_type}`,
    link,
  );
  return LinkSchema.parse(response.data);
};
