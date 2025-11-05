import { z } from "zod";

import { WorkflowUiEnum } from "./Workflows";

export const DocTypeEnums = z.enum([
  "video",
  "document",
  "link",
  "text",
  "image",
]);

export const DocumentationEnums = z.enum([
  "onboarding",
  "deliverable-tracking",
  "tagging",
  "thoughtspot",
  "release-notes",
  "dc-playbook",
  "faq",
  "intro-to-data-canvas",
  ...Object.values(WorkflowUiEnum.Values),
]);

export type TDocumentationEnums = z.infer<typeof DocumentationEnums>;

export const DocumentationSchema = z.object({
  doc_id: z.number(),
  doc_url: z.string(),
  doc_desc: z.string().min(1),
  doc_type: DocTypeEnums,
  ui_enum: DocumentationEnums,
  position: z.number(),
});
export const DocumentationRequestSchema = z.object({
  doc_id: z.number(),
  doc_url: z.string(),
  doc_desc: z.string().min(1),
  doc_type: DocTypeEnums,
  ui_enum: DocumentationEnums,
  position: z.number(),
  upload: z.boolean(),
});

export const CreateDocumentationSchema = z
  .object({
    doc_url: z.string().nullish(),
    doc_desc: z.string().min(1),
    doc_type: DocTypeEnums,
    ui_enum: DocumentationEnums,
    position: z.number(),
    upload: z.boolean(),
    file: z.custom<File[] | undefined>(),
  })
  .superRefine((data, ctx) => {
    if (
      data.doc_type === DocTypeEnums.Enum.video ||
      data.doc_type === DocTypeEnums.Enum.image ||
      data.doc_type === DocTypeEnums.Enum.document
    ) {
      if (!data.file) {
        return ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "File is required",
        });
      }
    }
    if (data.doc_type === DocTypeEnums.Enum.link && !data.doc_url) {
      return ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Document URL is required",
        path: ["doc_url"],
      });
    }
    return data;
  });

export type TDocumentation = z.infer<typeof DocumentationSchema>;
export type TDocumentationRequest = z.infer<typeof DocumentationRequestSchema>;
export type TCreateDocumentation = z.infer<typeof CreateDocumentationSchema>;
