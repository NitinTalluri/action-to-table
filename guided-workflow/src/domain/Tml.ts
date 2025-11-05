import { z } from "zod";

const TmlFileParamsSchema = z.object({
  lb_params: z.object({
    display_name: z.string(),
  }),
});

export type TTmlBlockAction = "copy" | "edit" | "restore";

export const TmlFileSchema = z.object({
  fileId: z.string(), // Not unique across buckets, but unique within a bucket
  ephemeral: z.boolean(),
  display_name: z.string(),
  bucketId: z.string(),
  parent_id: z.string().nullable(),
  originalBucket: z.string().nullable(), // If item was moved, this will be the original bucket it was - used for undo
  id: z.string(),
});

export type ITmlFile = z.infer<typeof TmlFileSchema>;

export const TmlResponseSchema = z.record(z.record(TmlFileParamsSchema));

export type ITmlResponse = z.infer<typeof TmlResponseSchema>;

export const convertTmlResponseToData = (
  response: ITmlResponse
): ITmlFile[] => {
  // Wrangle API response into a format that is easier to work with for the UI
  return Object.entries(response).reduce((acc, [bucket, files]) => {
    const items: ITmlFile[] = Object.entries(files).map(
      ([fileName, params]) => ({
        fileId: String(fileName),
        display_name: params.lb_params.display_name,
        ephemeral: false,
        bucketId: bucket,
        originalBucket: null,
        parent_id: null,
        id: `${bucket}-${fileName}`,
        allowCopy: bucket !== "common" && bucket !== "delete",
        allowEdit: bucket !== "common" && bucket !== "delete",
        allowRestore: false,
      })
    );
    return [...acc, ...items];
  }, [] as ITmlFile[]);
};

export interface ITmlData {
  [key: string]: ITmlFile[];
}

export interface ITmlPayload extends ITmlResponse {
  [bucket: string]: {
    [fileName: string]: {
      lb_params: {
        display_name: string;
        parent_id?: string;
      };
    };
  };
}

export const convertTmlDataToPayload = (data: ITmlData): ITmlPayload => {
  // Wrangle UI data into API's expected format
  // Top level keys are buckets
  return Object.entries(data).reduce((acc, [bucket, files]) => {
    const items = files.map((file) => ({
      [file.fileId.toString()]: {
        lb_params: {
          display_name: file.display_name,
          ...(file.parent_id !== null && { parent_id: file.parent_id }),
        },
      },
    }));
    return { ...acc, [bucket]: Object.assign({}, ...items) };
  }, {});
};

export type TBlockAction = "copy" | "edit" | "restore" | "remove";

export type TFetchTmlProps = {
  dc_engagement_id: number;
  canvas_id: number;
};
