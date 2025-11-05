import { SortingState, Updater } from "@tanstack/react-table";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";

const TABLE_SORTING_KEY = "table-sort";

// this is used as an extension of SortingState to allow for typed sorting
type TypedSortingState<T> = { desc: boolean; id: T }[];

export const useTableSort = <T extends string | number>({
  defaultSort,
  useRouter = false,
}: {
  defaultSort?: TypedSortingState<T>;
  useRouter?: boolean;
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  // get sort string from url
  const sortString = searchParams.get(TABLE_SORTING_KEY);
  const defaultSortAsSortingState = convertToSortingState(defaultSort || []);
  // set initial sort state
  const initialSort =
    useRouter && sortString?.length
      ? parseSortString(sortString)
      : defaultSortAsSortingState;
  // set sort state
  const [sorting, setSorting] = useState<SortingState>(initialSort || []);

  const onSortChange = (updater: Updater<SortingState>) => {
    const getState = (prevState: SortingState) =>
      updater instanceof Function ? updater(prevState) : updater;
    const updatedSorting = getState(sorting);

    if (useRouter) {
      setSearchParams((prevParams) => {
        prevParams.set(TABLE_SORTING_KEY, createSortString(updatedSorting));
        return prevParams;
      });
    }
    setSorting(updatedSorting);
  };

  useEffect(() => {
    // set search params to default sort if no sort string in url on initial render
    if (!useRouter || !defaultSort) return;
    if (typeof sortString === "string") return;
    // if no sort string in url, set it to default
    setSearchParams((prevParams) => {
      prevParams.set(
        TABLE_SORTING_KEY,
        createSortString(defaultSortAsSortingState),
      );
      return prevParams;
    });
  }, [
    defaultSort,
    defaultSortAsSortingState,
    setSearchParams,
    sortString,
    useRouter,
  ]);

  return [sorting, onSortChange] as const;
};

// takes a SortingState object and returns a string like "id-desc"
function createSortString(sorting: SortingState) {
  if (!sorting.length || typeof sorting[0] !== "object") return "";
  const [sort] = sorting;
  const { desc, id } = sort;
  return `${id}-${desc ? "desc" : "asc"}`;
}

// takes a string like "id-desc" and returns a SortingState object
function parseSortString(
  sortString: string,
  defaultSort?: SortingState,
): SortingState {
  const [id, desc] = sortString.split("-");
  if (!id || !desc) return defaultSort || [];
  if (desc !== "desc" && desc !== "asc") return defaultSort || [];
  return [{ id, desc: desc === "desc" }];
}

function convertToSortingState<T extends string | number>(
  sort: TypedSortingState<T>,
): SortingState {
  return sort.map((sort) => ({ ...sort, id: String(sort.id) }));
}
