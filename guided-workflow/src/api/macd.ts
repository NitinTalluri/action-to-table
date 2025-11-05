import { z } from "zod";

import client, { V2_WORKFLOW_URL } from "~/app/api";
import { ColumnsSchema, TColumnSchema } from "~/domain/ColumnResolver";
import {
  MACDInputResponseSchema,
  MACDToolSchemaAPIResponse,
  TMACDInputPost,
} from "~/domain/MACD";
import { GenericJobResponseSchema } from "~/domain/Workflows";
import { TParsedUpload } from "~/features/workflows/MACD/macd-audit/domain/UploadSchemas";
import { serializeError } from "~/utils";

import { compressData } from "./utils";

export const getMACDSchemas = async () => {
  const response = await client.get(`${V2_WORKFLOW_URL}/macd/schemas`);
  return MACDToolSchemaAPIResponse.parse(response.data);
};

export const getMACDInputs = async (engagementID: number) => {
  const response = await client.get(
    `${V2_WORKFLOW_URL}/macd/submissions/${engagementID}`,
  );
  return MACDInputResponseSchema.parse(response.data);
};

export const postMACDInput = async (payload: TMACDInputPost) => {
  const { rows, ...rest } = payload;

  const compressedRowData = await compressData(rows);

  const formData = new FormData();
  formData.append("data", compressedRowData, "macd_input.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    `${V2_WORKFLOW_URL}/macd`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  const parsedResponse = GenericJobResponseSchema.safeParse(response.data);
  if (!parsedResponse.success) {
    console.error(serializeError(parsedResponse.error));
    return null;
  }
  return parsedResponse.data;
};

export const uploadMACDAudit = async (payload: TParsedUpload) => {
  const { rows, ...rest } = payload;

  const formData = new FormData();

  if (rest.schema_type !== "skip") {
    const compressedRowData = await compressData(rows);
    formData.append("data", compressedRowData, "macd_audit.json.gz");
  }
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    `${V2_WORKFLOW_URL}/macd/audit`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  const parsedResponse = GenericJobResponseSchema.safeParse(response.data);
  if (!parsedResponse.success) {
    console.error(serializeError(parsedResponse.error));
    return null;
  }
  return parsedResponse.data;
};

export const getMACDHistoricalSchemas = async (): Promise<TColumnSchema[]> => {
  // TODO - This should call API endpoint instead of importing JSON directly
  const resolverJson = await import(
    "~/features/workflows/MACD/macd-upload/historical/domain/resolver.json"
  );
  const arr = Object.values(resolverJson.default ?? resolverJson);
  return await ColumnsSchema.parseAsync(arr);
};
