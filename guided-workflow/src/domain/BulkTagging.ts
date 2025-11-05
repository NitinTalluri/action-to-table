import { z } from "zod";

export type TBulkTaggingResponse = {
  message: string;
};

export const BulkTaggingResponseSchema = z.object({
  message: z.string(),
});

export type TBulkTaggingResponseSuccess = [TBulkTaggingResponse, number];

export const BulkTaggingFullResponseSchema = z.tuple([
  BulkTaggingResponseSchema,
  z.number(),
]);
