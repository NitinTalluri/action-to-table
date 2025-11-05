import { z } from "zod";

export const truthyEnum = z.enum(["T", "F"] as const);

type TTruthyEnum = z.infer<typeof truthyEnum>;
type TTruthy = boolean | TTruthyEnum;
export const isTruthy = (v: TTruthy): boolean => {
  if (typeof v === "boolean") {
    return v;
  }
  return v === "T";
};
