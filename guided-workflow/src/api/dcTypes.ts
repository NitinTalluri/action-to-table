import client, { V2_URL } from "~/app/api";
import { parseDcTypes } from "~/domain/DcTypes";
import { TDcTypes } from "~/domain/DcTypes/schema";

export const getDcTypes = async (): Promise<TDcTypes> => {
  const response = await client.get(`${V2_URL}/dc_types`);
  return parseDcTypes(response.data);
};
