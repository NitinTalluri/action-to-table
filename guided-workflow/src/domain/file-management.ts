import { z } from "zod";

export const ArchivedLiveboardsSchema = z.object({
  lb_type: z.string(),
  liveboard_id: z.number(),
  display_name: z.string(),
  create_dtm: z.string().nullable(),
  location: z.string(),
});

export type TArchivedLiveboard = z.infer<typeof ArchivedLiveboardsSchema>;

export const ArchivedLiveboardsResponseSchema = z.object({
  engagement_id: z.number(),
  canvas_id: z.number(),
  live_boards: z.array(ArchivedLiveboardsSchema),
});

export type TArchivedLiveboardsResponse = z.infer<
  typeof ArchivedLiveboardsResponseSchema
>;
