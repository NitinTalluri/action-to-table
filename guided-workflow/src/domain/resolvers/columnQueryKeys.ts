import { TColumnSchema } from "~/domain/ColumnResolver";
import { TColumnRegistryName } from "~/domain/resolvers/columnRegistry";

const getSchemaKey = (schema: string) => {
  return schema.split("").reduce((acc, char) => {
    const charCode = char.charCodeAt(0);
    return acc + charCode;
  }, 0);
};
const getSchemasKey = (schemas: TColumnSchema[]) => {
  return schemas
    .map((s) => getSchemaKey(s.name))
    .reduce((acc, key) => acc + key, 0);
};
export const columnQueryKeys = {
  all: ["sheetReader"] as const,
  list: (fileName: string) => [...columnQueryKeys.all, fileName] as const,
  detail: (fileName: string, sheetName: string, schemas: TColumnSchema[]) =>
    [
      ...columnQueryKeys.list(fileName),
      sheetName,
      getSchemasKey(schemas),
    ] as const,
  resolvedColumns: (
    fileName: string,
    sheetName: string,
    schemas: TColumnSchema[],
  ) =>
    [
      ...columnQueryKeys.detail(fileName, sheetName, schemas),
      "resolved",
      "columns",
    ] as const,
  resolvedData: (
    fileName: string,
    sheetName: string,
    schemas: TColumnSchema[],
  ) =>
    [
      ...columnQueryKeys.detail(fileName, sheetName, schemas),
      "resolved",
      "data",
    ] as const,
  validatedData: (
    fileName: string,
    sheetName: string,
    registryName: TColumnRegistryName,
  ) =>
    [
      ...columnQueryKeys.list(fileName),
      sheetName,
      registryName,
      "validated",
      "data",
    ] as const,
};
