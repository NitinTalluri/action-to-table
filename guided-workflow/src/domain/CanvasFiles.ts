import { z } from "zod";

const createCanvasFileTypes = z.enum([
  "SMART_ACCOUNT",
  "MCE",
  "ACAT",
  "CONTRACTS",
  "PARTY",
]);

export const UnifiedCanvasFileSchema = z.object({
  name: createCanvasFileTypes,
});
export type TCreateCanvasFileTypes = z.infer<typeof createCanvasFileTypes>;
