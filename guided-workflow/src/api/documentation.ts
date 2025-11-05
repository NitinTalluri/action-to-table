import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  DocumentationRequestSchema,
  DocumentationSchema,
  TCreateDocumentation,
  TDocumentation,
  TDocumentationEnums,
} from "~/domain/Documentation";

export const getDocumentation = async (uiEnum: TDocumentationEnums) => {
  const response = await client.get(
    `${V2_URL}/documentation?ui_enum=${uiEnum}`,
  );
  return z.array(DocumentationSchema).parse(response.data);
};

export const createDocumentation = async (
  data: TCreateDocumentation,
): Promise<TDocumentation> => {
  const formData = new FormData();
  formData.append("payload", JSON.stringify(data));
  if (data.file) {
    formData.append("file", data.file[0]);
  }
  const response = await client.post(`${V2_URL}/documentation`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return DocumentationSchema.parse(response.data);
};

export const updateDocumentation = async (
  data: z.infer<typeof DocumentationRequestSchema>,
): Promise<TDocumentation> => {
  const response = await client.patch(
    `${V2_URL}/documentation/${data.doc_id}`,
    data,
  );
  return DocumentationSchema.parse(response.data);
};

export const deleteDocumentation = async (
  docId: number,
): Promise<TDocumentation> => {
  const response = await client.delete(`${V2_URL}/documentation/${docId}`);
  return DocumentationSchema.parse(response.data);
};
