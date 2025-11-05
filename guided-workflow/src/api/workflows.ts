import { z } from "zod";

import { compressData } from "~/api/utils";
import client, { V2_WORKFLOW_URL } from "~/app/api";
import { TSerialTaggingPayloadOutput } from "~/domain/SerialTagging";
import {
  SnifReportResponseSchema,
  TSnifReportPayload,
  TSnifReportResponseInput,
  TSnifReportResponseSuccess,
} from "~/domain/SnifReport";
import { BulkTaggingPayload, TagHistoryPayload } from "~/domain/Tagset";
import {
  GenericJobResponseSchema,
  TDetailNotification,
  TLogSignOffRequestSchema,
  WorkflowNotificationDetailSchema,
  WorkflowNotificationSummarySchema,
  WorkflowTreeSchema,
} from "~/domain/Workflows";
import { TDeferFormBody } from "~/features/workflows/account-management/log-signoff/DeferForm";
import { TPreparedInstanceTagging } from "~/features/workflows/tagging/instance-tagging/hooks/useTaggingApi";
import { TParsedCollectorUpload } from "~/features/workflows/uploads/collector-file/domain/CollectorUpload";
import { TParsedUpload as TParsedCustomerUpload } from "~/features/workflows/uploads/customer-file/domain/UploadSchema";
import { TParsedUpload as TParsedSEAUpload } from "~/features/workflows/uploads/sea/domain/UploadSchemas";
import { serializeError } from "~/utils";

export const getWorkflowTree = async () => {
  const response = await client.get(`${V2_WORKFLOW_URL}/actions`);
  const parsedData = WorkflowTreeSchema.safeParse(response.data);
  if (!parsedData.success) {
    console.error(parsedData.error);
    throw new Error("Invalid tree data");
  }
  return parsedData.data;
};

export const getWorkflowNotifications = async (
  engagementId: number,
  lastActivity = "",
) => {
  const response = await client.get(
    `${V2_WORKFLOW_URL}/notifications/${engagementId}${lastActivity ? `?last_activity=${lastActivity}` : ""}`,
  );
  const parsedData = WorkflowNotificationSummarySchema.array().safeParse(
    response.data,
  );
  if (!parsedData.success) {
    console.error(parsedData.error);
    throw new Error("Invalid notifications data");
  }
  return parsedData.data;
};

export const getWorkflowNotification = async (
  engagementId: number,
  notificationId: number,
): Promise<TDetailNotification> => {
  const response = await client.get(
    `${V2_WORKFLOW_URL}/notifications/${engagementId}/${notificationId}`,
  );
  const parsedData = WorkflowNotificationDetailSchema.safeParse(response.data);
  if (!parsedData.success) {
    console.error(parsedData.error);
    throw new Error("Invalid notification data");
  }
  return parsedData.data;
};

export const postWorkflowSignOff = async (
  data: TDeferFormBody | TLogSignOffRequestSchema,
) => {
  const response = await client.post(`${V2_WORKFLOW_URL}/sign_off`, data);
  return response.data;
};

export const uploadCustomerFile = async (payload: TParsedCustomerUpload) => {
  const { rows, ...rest } = payload;

  const url = `${V2_WORKFLOW_URL}/evidence_uploads/customer`;
  const compressedRowData = await compressData(rows);

  const formData = new FormData();
  formData.append("data", compressedRowData, "customer_file.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    url,
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

export type TUploadCollectorFile = TParsedCollectorUpload & {
  rows: Record<string, unknown>[];
};

export const uploadCollectorFile = async (payload: TUploadCollectorFile) => {
  const { rows, ...rest } = payload;
  const url = `${V2_WORKFLOW_URL}/evidence_uploads/collector`;
  const compressedRowData = await compressData(rows);
  const formData = new FormData();
  formData.append("data", compressedRowData, "collector_file.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    url,
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

export const generateSiteReport = async (engagementId: number) => {
  const response = await client.post(`${V2_WORKFLOW_URL}/lookups/site-report`, {
    engagement_id: engagementId,
  });
  return response.data;
};

export const generateACATReport = async (engagementId: number) => {
  const response = await client.post(
    `${V2_WORKFLOW_URL}/lookups/acat-discovery`,
    {
      engagement_id: engagementId,
    },
  );
  return response.data;
};

export const generateHostnameRelinkReport = async (engagementId: number) => {
  const response = await client.post(
    `${V2_WORKFLOW_URL}/lookups/host-name-relink`,
    {
      engagement_id: engagementId,
    },
  );
  return response.data;
};

export const generateHostnameSiteMovesReport = async (engagementId: number) => {
  const response = await client.post(
    `${V2_WORKFLOW_URL}/lookups/host-name-site-moves`,
    {
      engagement_id: engagementId,
    },
  );
  return response.data;
};

export const generateSNIFReport = async (
  data: TSnifReportPayload,
): Promise<TSnifReportResponseSuccess> => {
  const response = await client.post<TSnifReportResponseInput>(
    `${V2_WORKFLOW_URL}/lookups/snif-report`,
    data,
  );

  const parsedResponse = SnifReportResponseSchema.safeParse(response.data);
  if (!parsedResponse.success) {
    console.error(serializeError(parsedResponse.error));
    throw new Error(serializeError(parsedResponse.error));
  }
  const parsedResponseData = parsedResponse.data;
  if (!parsedResponseData.success) {
    throw new Error(parsedResponseData.message);
  }

  return parsedResponseData;
};

export const postBulkTagging = async (payload: BulkTaggingPayload) => {
  const { row_data, ...rest } = payload;

  const compressedRowData = await compressData(row_data);

  const formData = new FormData();
  formData.append("data", compressedRowData, "bulk_tagging.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    `${V2_WORKFLOW_URL}/bulk_instance_tagging`,
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
    throw null;
  }

  return parsedResponse.data;
};

export const getTagHistory = async (payload: TagHistoryPayload) => {
  const { ids, ...rest } = payload;

  const url = `${V2_WORKFLOW_URL}/lookups/tag-history`;
  const compressedRowData = await compressData(ids);

  const formData = new FormData();
  formData.append("data", compressedRowData, "tag_history.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    url,
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

export const postInstanceTagging = async (
  payload: TPreparedInstanceTagging["payload"],
) => {
  const { instance_ids, ...rest } = payload;

  const url = `${V2_WORKFLOW_URL}/instance_tagging`;
  const compressedRowData = await compressData(instance_ids);

  const formData = new FormData();
  formData.append("data", compressedRowData, "instance_tagging.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    url,
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

export const postSerialTagging = async (
  payload: TSerialTaggingPayloadOutput,
) => {
  const { serial_numbers, ...rest } = payload;

  const url = `${V2_WORKFLOW_URL}/serial_tagging`;
  const compressedRowData = await compressData(
    serial_numbers.map((serial_number) => ({ serial_number })),
  );

  const formData = new FormData();
  formData.append("data", compressedRowData, "serial_tagging.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    url,
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

export const postSeaFile = async (payload: TParsedSEAUpload) => {
  const { rows, ...rest } = payload;

  const compressedRowData = await compressData(rows);

  const formData = new FormData();
  formData.append("data", compressedRowData, "sea_upload.json.gz");
  formData.append("payload", JSON.stringify(rest));

  const response = await client.post<z.input<typeof GenericJobResponseSchema>>(
    `${V2_WORKFLOW_URL}/sea_upload`,
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
