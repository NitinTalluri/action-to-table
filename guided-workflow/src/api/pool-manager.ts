import client, { V2_URL } from "~/app/api";

export const putPoolManager = async () => {
  const url = `${V2_URL}/manager/pool_manager`;
  const response = await client.put(url);

  return response.data;
};
