import { z } from "zod";

export const ColumnSchema = z.object({
  name: z.string().describe("The internal representation of the column name"),
  displayName: z
    .string()
    .describe(
      "When referring to the column in UI, this is the name that will be displayed. It will be treated as a P1 alias",
    ),
  aliases: z
    .array(z.string())
    .catch([])
    .describe(
      "Aliases for the column name. Treated as P2 aliases. Cannot be the same as another column's name or alias, and cannot be empty or whitespace",
    ),
});

export type TColumnSchema = z.infer<typeof ColumnSchema>;

export const ColumnsSchema = z
  .array(ColumnSchema)
  .superRefine((columns, ctx) => {
    const columnNamesSeen = new Set<string>();
    const displayNamesSeen = new Set<string>();
    const aliasMap = new Map<string, string>(); // [displayName, alias] -> name

    // Check that all column names, display names are unique after lowercasing
    columns.forEach((col, index) => {
      const lowerName = col.name.toLowerCase();
      const lowerDisplayName = col.displayName.toLowerCase();
      if (columnNamesSeen.has(lowerName)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Duplicate column name: ${col.name}`,
          path: [index, "name"],
        });
      }
      columnNamesSeen.add(lowerName);
      if (displayNamesSeen.has(lowerDisplayName)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Duplicate display name: ${col.displayName}`,
          path: [index, "displayName"],
        });
      }
      displayNamesSeen.add(lowerDisplayName);
    });

    // Check aliases for each column to ensure no conflicts
    // 1. aliases must only refer to their own column name, and not map to another column's name
    // 2. aliases must not be empty or whitespace

    columns.forEach((col, index) => {
      const lowerName = col.name.toLowerCase();
      const lowerDisplayName = col.displayName.toLowerCase();
      // lowerDisplayName is P1 alias
      if (
        aliasMap.has(lowerDisplayName) &&
        aliasMap.get(lowerDisplayName) !== lowerName
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Display name '${col.displayName}' conflicts with another column's alias`,
          path: [index, "displayName"],
        });
      }
      aliasMap.set(lowerDisplayName, lowerName);
    });

    columns.forEach((col, index) => {
      // Handling aliases now, P2
      const lowerName = col.name.toLowerCase();
      const lowerAliases = col.aliases.map((alias) => alias.toLowerCase());
      lowerAliases.forEach((alias, aliasIndex) => {
        if (alias.length === 0 || alias.trim().length === 0) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Alias '${col.aliases[aliasIndex]}' for column '${col.name}' is empty or whitespace`,
            path: [index, "aliases", aliasIndex],
          });
        }
        const resolvedAlias = aliasMap.get(alias);
        if (resolvedAlias && resolvedAlias !== lowerName) {
          // This alias refers to another column's name
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Alias '${col.aliases[aliasIndex]}' for column '${col.name}' would conflict with another column's name ('${resolvedAlias}')`,
            path: [index, "aliases", aliasIndex],
          });
        }
        if (columnNamesSeen.has(alias) && alias !== lowerName) {
          // This alias is the same as another column's name
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Alias '${col.aliases[aliasIndex]}' for column '${col.name}' conflicts with another column name`,
            path: [index, "aliases", aliasIndex],
          });
        }

        if (!resolvedAlias) {
          aliasMap.set(alias, lowerName);
        }
      });
    });
  });
export type TColumnsSchema = z.infer<typeof ColumnsSchema>;

export type TResolvedColumn = {
  displayName: string;
  index: number;
  resolvedSchema: TColumnSchema;
};

export type TUnresolvedColumn = {
  displayName: string;
  index: null;
  resolvedSchema: null;
};
