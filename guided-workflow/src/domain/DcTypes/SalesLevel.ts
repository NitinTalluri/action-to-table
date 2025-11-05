import z from "zod";

export const SalesLevelSchema = z.object({
  node_level1: z.string().nullable(),
  node_level2: z.string().nullable(),
  node_level3: z.string().nullable(),
  node_level4: z.string().nullable(),
  node_segment: z.string().nullable(),
});

export type TSalesLevel = z.infer<typeof SalesLevelSchema>;
