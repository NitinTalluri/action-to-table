import client, { V2_WORKFLOW_URL } from "~/app/api";
import { PresignedUrlResponseSchema } from "~/domain/Workflows";

export const getPresignedUrl = async (urlToPresign: string) => {
  const response = await client.post(`${V2_WORKFLOW_URL}/downloads`, {
    url: urlToPresign,
  });
  const parsedData = PresignedUrlResponseSchema.safeParse(response.data);
  if (!parsedData.success) {
    console.error(parsedData.error);
    throw new Error("Invalid presigned url data");
  }
  return parsedData.data;
};
