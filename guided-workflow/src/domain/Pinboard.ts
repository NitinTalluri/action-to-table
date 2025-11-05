import { z } from "zod";

export const PinboardSchema = z.object({
  guid: z.string(),
  pinboard_name: z.string(),
});

export type IPinboard = z.infer<typeof PinboardSchema>;
