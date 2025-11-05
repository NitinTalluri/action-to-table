import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import { TEngagement } from "~/domain/Engagement";
import {
  TUserDefinedTypeArray,
  TUserDefinedTypeCreate,
  TUserDefinedTypeDelete,
  TUserDefinedTypeUpdate,
  UserDefinedType,
  UserDefinedTypeArray,
  UserDefinedTypeUpdateResponse,
} from "~/domain/UserDefinedTypes";

export const getUserDefinedTypes = async (
  dc_engagement_id: TEngagement["dc_engagement_id"],
): Promise<TUserDefinedTypeArray> => {
  const response = await client.get<z.input<typeof UserDefinedTypeArray>>(
    `${V2_URL}/udt/${dc_engagement_id}`,
  );
  return UserDefinedTypeArray.parse(response.data);
};

export const getUserDefinedTypesByFieldName = async (
  dc_engagement_id: TEngagement["dc_engagement_id"],
  field_name: string,
): Promise<TUserDefinedTypeArray> => {
  const response = await client.get<z.input<typeof UserDefinedTypeArray>>(
    `${V2_URL}/udt/${dc_engagement_id}?field_name=${field_name}`,
  );
  return UserDefinedTypeArray.parse(response.data);
};

export const createUserDefinedType = async (data: TUserDefinedTypeCreate) => {
  const response = await client.post<z.input<typeof UserDefinedType>>(
    `${V2_URL}/udt`,
    data,
  );
  return UserDefinedType.parse(response.data);
};

export const editUserDefinedType = async (data: TUserDefinedTypeUpdate) => {
  /**
   * Gotcha: If the type is edited to match a value of a deleted user defined type, this id will be updated.
   * We include the originalId in the response to help the client keep track of the original id.
   */
  const originalId = data.id;
  const response = await client.patch<z.input<typeof UserDefinedType>>(
    `${V2_URL}/udt`,
    data,
  );
  return UserDefinedTypeUpdateResponse.parse({ ...response.data, originalId });
};

export const deleteUserDefinedType = async (data: TUserDefinedTypeDelete) => {
  const response = await client.delete<z.input<typeof UserDefinedType>>(
    `${V2_URL}/udt`,
    { data },
  );
  return UserDefinedType.parse(response.data);
};
