import { z } from "zod";

export const EngagementTaskSchema = z.object({
  tag_names: z.array(z.string()).catch([]),
  tag_ids: z.array(z.number()).catch([]),
  tagset_names: z.array(z.string()).catch([]),
  tagset_ids: z.array(z.number()).catch([]),
  thoughtspot_id: z.number(),
  canvas_id: z.number(),
  canvas: z.string(),
  dc_engagement_id: z.number(),
  count_instances: z.number(),
  comment: z.string(),
  create_dtm: z.string(),
  created_by: z.string(),
  user_action: z.enum(["set", "unset", "extract"]),
  extract_state: z.enum(["pending", "processed", "deleted"]),
});

export const EngagementTaskSchemaArray = z.array(EngagementTaskSchema);

export type IEngagementTaskAPI = z.infer<typeof EngagementTaskSchema>;
