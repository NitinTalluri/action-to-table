import { CellContext, Table } from "@tanstack/react-table";
import { useEffect, useState } from "react";
import { z } from "zod";

const editableTableSchema = z.object({
  meta: z.object({
    updateData: z.function(
      z.tuple([z.number(), z.string(), z.unknown()]),
      z.void(),
    ),
  }),
});

const getTableMeta = <T,>(table: Table<T>) => {
  const parsed = editableTableSchema.safeParse(table.options);
  if (!parsed.success) {
    return null;
  }
  return parsed.data.meta;
};

type EditableCellProps<T> = {
  ctx: CellContext<T, unknown>;
} & (
  | {
      variant: "text" | "date" | "number";
      options?: never;
    }
  | {
      variant: "select";
      // options are not optional if variant is select
      options: { id: number | string; value: string }[];
    }
);

export const EditableCell = <T,>({
  ctx,
  variant,
  options,
}: EditableCellProps<T>) => {
  const {
    getValue,
    table,
    row: { index },
    column,
  } = ctx;
  const initialValue = getValue();
  // We need to keep and update the state of the cell normally
  const [value, setValue] = useState(initialValue);
  const tableMeta = getTableMeta(table);

  const onBlur = () => {
    tableMeta?.updateData(index, column.id, value);
  };

  // If the initialValue is changed external, sync it up with our state
  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  if (variant === "select") {
    return (
      <select
        style={{
          padding: ".5rem",
          width: "100%",
          border: "none",
        }}
        value={Number(initialValue)}
        onChange={(e) =>
          tableMeta?.updateData(index, column.id, e.target.value)
        }
      >
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.value}
          </option>
        ))}
      </select>
    );
  }

  return (
    <input
      type={variant}
      style={{
        background: "transparent",
        border: "none",
        padding: ".5rem",
        width: "100%",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
      value={String(value)}
      onChange={(e) => setValue(e.target.value)}
      onBlur={onBlur}
    />
  );
};
