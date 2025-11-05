import { z } from "zod";

export const DefaultSchema = z.object({
  message: z.string().nullish(),
});
