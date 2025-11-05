import { useState } from "react";

export const useFilterResults = <T>({
  filterables,
  conditions,
  defaultType = "OR",
  query,
}: {
  filterables: T[];
  conditions: ((q: string, item: T) => boolean)[];
  defaultType?: "AND" | "OR";
  query?: string;
}) => {
  const [internalQuery, setInternalQuery] = useState("");
  const [filterType, setFilterType] = useState<"AND" | "OR">(defaultType);

  const q = query || internalQuery;

  // Function to determine if an item matches based on the query words and conditions
  const itemMatchesConditions = (filterable: T) => {
    if (!q.length) return true; // If no query, potentially return all items
    return conditions[filterType === "AND" ? "every" : "some"]((condition) =>
      condition(q, filterable),
    );
  };

  const filtered = filterables.filter(itemMatchesConditions);

  return {
    filtered,
    filterType,
    setFilterType,
    setQuery: setInternalQuery,
    query: q,
  };
};
