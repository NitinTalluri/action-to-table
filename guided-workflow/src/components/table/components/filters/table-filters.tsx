import { Column } from "@tanstack/react-table";

import { getMeta, TableMetaEnums } from "../../utils";
import { AutocompleteFilter } from "./autocomplete-filter";
import { DateRangeFilter } from "./date-range-filter";
import { MultiAutocompleteFilter } from "./multi-autocomplete-filter";
import { MultiSelectFilter } from "./multi-select-filter";
import { NumberRangeFilter } from "./number-range-filter";
import { SelectFilter } from "./select-filter";

export const TableFilters = <T,>({
  column,
  selectOptions,
}: {
  column: Column<T, unknown>;
  // record key must correspond to column id
  selectOptions: Record<
    string,
    { id: string | number | boolean; value: string }[]
  >;
}) => {
  const { filterVariant } = getMeta(column);

  switch (filterVariant) {
    case TableMetaEnums.Enum.select: {
      const options =
        column.id in selectOptions
          ? selectOptions[column.id as keyof typeof selectOptions]
          : [];
      return <SelectFilter column={column} options={options} />;
    }
    case TableMetaEnums.Enum["multi-select"]: {
      const options =
        column.id in selectOptions
          ? selectOptions[column.id as keyof typeof selectOptions]
          : [];
      return <MultiSelectFilter column={column} options={options} />;
    }
    case TableMetaEnums.Enum["multi-select-no-facet"]: {
      const options =
        column.id in selectOptions
          ? selectOptions[column.id as keyof typeof selectOptions]
          : [];
      return (
        <MultiSelectFilter
          column={column}
          options={options}
          isFaceted={false}
        />
      );
    }
    case TableMetaEnums.Enum.date:
      return <DateRangeFilter column={column} />;
    case TableMetaEnums.Enum.range:
      return <NumberRangeFilter column={column} />;
    case TableMetaEnums.Enum["multi-autocomplete"]:
      return <MultiAutocompleteFilter column={column} />;
    default:
      return <AutocompleteFilter column={column} />;
  }
};
