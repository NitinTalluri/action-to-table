import { z } from "zod";

import { macdHistoricalColumnSchemas } from "~/features/workflows/MACD/macd-upload/historical/domain/schemas";
import invariant from "~/utils/invariant";

type TAllowedSchemaTypes = string | null | number | Date;
type TZodAllowedSchemaTypes = z.ZodType<TAllowedSchemaTypes>;

export const ColumnRegistryNameEnum = z.enum([
  "macdHistorical",
  // Add additional registry names as needed
]);

export type TColumnRegistryName = z.infer<typeof ColumnRegistryNameEnum>;

export interface IColumnSchemaResolver {
  columnSchemas: Map<string, TZodAllowedSchemaTypes>;
  addColumnSchema: <T extends TZodAllowedSchemaTypes>(
    name: string,
    schema: T,
  ) => void;
  addColumnSchemas: <T extends TZodAllowedSchemaTypes>(
    schemas: Record<string, T>,
  ) => void;
  getColumnSchema: (name: string) => TZodAllowedSchemaTypes | undefined;
  buildObjectSchema: <Cols extends string[]>(
    cols: Cols,
  ) => z.ZodObject<Record<string, TZodAllowedSchemaTypes>>;
}

export interface IColumnSchemaResolverFactory {
  registries: Map<TColumnRegistryName, IColumnSchemaResolver>;
  getColumnResolver: (name: TColumnRegistryName) => IColumnSchemaResolver;
  registerColumnResolver: <T extends TZodAllowedSchemaTypes>(
    registryName: TColumnRegistryName,
    schemas: Record<string, T>,
  ) => void;
}

class ColumnResolver implements IColumnSchemaResolver {
  columnSchemas: Map<string, TZodAllowedSchemaTypes> = new Map();

  addColumnSchema<T extends TZodAllowedSchemaTypes>(
    name: string,
    schema: T,
  ): void {
    this.columnSchemas.set(name, schema);
  }

  addColumnSchemas<T extends TZodAllowedSchemaTypes>(
    schemas: Record<string, T>,
  ): void {
    Object.entries(schemas).forEach(([name, schema]) => {
      this.addColumnSchema(name, schema);
    });
  }

  getColumnSchema(name: string): TZodAllowedSchemaTypes | undefined {
    return this.columnSchemas.get(name);
  }

  buildObjectSchema(
    cols: string[],
  ): z.ZodObject<Record<string, TZodAllowedSchemaTypes>> {
    const uniqueCols = Array.from(new Set(cols)); // Ensure unique column names
    const missingColumns: string[] = uniqueCols.filter(
      (col) => !this.columnSchemas.has(col),
    );
    if (missingColumns.length > 0) {
      console.warn(`Missing column schemas for: ${missingColumns.join(", ")}`);
      // TODO - decide if this is error
      // throw new Error(`Missing column schemas for: ${missingColumns.join(', ')}`);
    }
    const foundColumns: string[] = uniqueCols.filter((col) =>
      this.columnSchemas.has(col),
    );
    return z.object(
      foundColumns.reduce(
        (acc, col) => {
          const schema = this.columnSchemas.get(col);
          invariant(
            schema,
            `Schema for column ${col} not found - should not be possible`,
          );
          acc[col] = schema;
          return acc;
        },
        {} as Record<string, TZodAllowedSchemaTypes>,
      ),
    );
  }
}

export class ColumnSchemaFactory implements IColumnSchemaResolverFactory {
  registries: Map<TColumnRegistryName, ColumnResolver> = new Map();
  getColumnResolver(name: TColumnRegistryName): IColumnSchemaResolver {
    const resolver = this.registries.get(name);
    invariant(resolver, `Column resolver for ${name} not found`);
    return resolver;
  }

  registerColumnResolver<T extends TZodAllowedSchemaTypes>(
    registryName: TColumnRegistryName,
    schemas: Record<string, T>,
  ): void {
    if (this.registries.has(registryName)) {
      console.warn(
        `Column resolver for ${registryName} already exists, updating schemas`,
      );
    }
    const resolver = new ColumnResolver();
    resolver.addColumnSchemas(schemas);
    this.registries.set(registryName, resolver);
  }
}

export const columnSchemaFactory: IColumnSchemaResolverFactory =
  new ColumnSchemaFactory();
columnSchemaFactory.registerColumnResolver(
  ColumnRegistryNameEnum.enum.macdHistorical,
  macdHistoricalColumnSchemas,
);
