import { z } from "zod";

import isDev from "~/utils/isDev";

// This function takes in a data and a schema and returns the parsed data...
// ...if the data is valid according to the schema.
// If the data is invalid, it returns undefined and logs the error to the console
export const returnParsedData = <T extends z.ZodTypeAny>(
  data: unknown,
  schema: T,
) => {
  if (!data) return undefined;
  const parsed = schema.safeParse(data);
  if (parsed.success) {
    return parsed.data as z.infer<T>;
  }
  if (isDev) console.warn(parsed.error.issues);
  return undefined;
};

export const returnParsedArrayData = <T extends z.ZodRawShape>(
  data: unknown,
  schema: z.ZodArray<z.ZodObject<T>>,
) => {
  if (!data) return [];
  const parsed = schema.safeParse(data);
  if (parsed.success) {
    return parsed.data;
  }
  if (isDev) console.warn(parsed.error.issues);
  return [];
};
