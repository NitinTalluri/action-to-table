import { z } from "zod";

const EmptyLikeStrings = [
  "-",
  "--",
  "---",
  "",
  "#N/A",
  "#N/A N/A",
  "#NA",
  "-1.#IND",
  "-1.#QNAN",
  "-NaN",
  "-nan",
  "1.#IND",
  "1.#QNAN",
  "<NA>",
  "N/A",
  "NA",
  "NULL",
  "NaN",
  "None",
  "n/a",
  "nan",
  "null",
];

const ValidIntegerRegex = /^\d+$/;
const ValidFloatRegex = /^\d*\.?\d+$/;
const RemoveControlRegex = /\p{C}/gu;

export const DateFormatEnum = z.enum([
  "yyyy-MM-dd",
  "dd/MM/yyyy",
  "MM/dd/yyyy",
  "dd-MM-yyyy",
  "dd-MMM-yyyy",
  "MM-dd-yyyy",
]);

export type TDateFormatEnum = z.infer<typeof DateFormatEnum>;

export const ISOFormat = z.literal("yyyy-MM-dd");

export const CellString = z.coerce
  .string()
  .nullish()
  .transform((val) => val && val.replace(RemoveControlRegex, "").trim());

export const stringSuperRefine = (
  val: string | undefined,
  ctx: z.RefinementCtx,
  required: boolean,
) => {
  if (!val || val === "") {
    if (required) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Value is required.",
      });
    }
    return;
  }

  val = val.trim();
  if (EmptyLikeStrings.includes(val)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "String cannot be empty.",
    });
  }

  if (RemoveControlRegex.test(val)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "String contains invalid characters.",
    });
  }
};

export const numberSuperRefine = (
  val: string | undefined,
  ctx: z.RefinementCtx,
  required: boolean,
) => {
  if (!val || val === "") {
    if (required) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Value is required.",
      });
    }
    return;
  }

  const parsedNumber = parseInt(val);
  if (isNaN(parsedNumber)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Invalid number format.",
    });
    return;
  }

  if (!ValidIntegerRegex.test(val)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Invalid number format.",
    });
    return;
  }

  if (parsedNumber < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Number cannot be negative.",
    });
  }
};

export const floatSuperRefine = (
  val: string | undefined,
  ctx: z.RefinementCtx,
  required: boolean,
) => {
  if (!val || val === "") {
    if (required) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Value is required.",
      });
    }
    return;
  }

  const parsedFloat = parseFloat(val);
  if (isNaN(parsedFloat)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Invalid number format.",
    });
    return;
  }

  if (!ValidFloatRegex.test(val)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Invalid number format.",
    });
    return;
  }

  if (parsedFloat < 0) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Number cannot be negative.",
    });
  }
};

export const booleanSuperRefine = (
  val: string | undefined,
  ctx: z.RefinementCtx,
  required: boolean,
) => {
  if (!val || val === "") {
    if (required) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Value is required.",
      });
    }
    return;
  }

  const lowerVal = val.toLowerCase();
  if (lowerVal !== "true" && lowerVal !== "false") {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "Invalid boolean format. Expected 'true' or 'false'.",
    });
  }
};
