import { PaginationState, Updater } from "@tanstack/react-table";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";

// ? default page size app pref?
const DEFAULT_PAGINATION = { pageSize: 10, pageIndex: 0 };
const TABLE_PAGINATION_KEY = "table-pagination";

export const useTablePagination = ({
  defaultPagination,
  useRouter = false,
}: {
  defaultPagination?: PaginationState;
  useRouter?: boolean;
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  // get pagination string from url
  const paginationString = searchParams.get(TABLE_PAGINATION_KEY);
  // set initial pagination state
  const initialPagination =
    useRouter && paginationString?.length
      ? parsePaginationString(paginationString)
      : defaultPagination;
  // set pagination state
  const [pagination, setPagination] = useState<PaginationState>(
    initialPagination || DEFAULT_PAGINATION,
  );

  const onPaginationChange = (updater: Updater<PaginationState>) => {
    const getState = (prevState: PaginationState) =>
      updater instanceof Function ? updater(prevState) : updater;
    const updatedPagination = getState(pagination);

    if (useRouter) {
      setSearchParams((prevParams) => {
        prevParams.delete(TABLE_PAGINATION_KEY);
        prevParams.set(
          TABLE_PAGINATION_KEY,
          createPaginationString(updatedPagination),
        );
        return prevParams;
      });
    }
    setPagination(updatedPagination);
  };

  useEffect(() => {
    // set search params to default pagination if no pagination string in url on initial render
    if (!useRouter || !defaultPagination) return;
    if (typeof paginationString === "string") return;
    // if no pagination string in url, set it to default
    setSearchParams((prevParams) => {
      prevParams.set(
        TABLE_PAGINATION_KEY,
        createPaginationString(defaultPagination),
      );
      return prevParams;
    });
  }, [defaultPagination, paginationString, setSearchParams, useRouter]);

  return [pagination, onPaginationChange] as const;
};

// takes a PaginationState object and returns a string like "0-10"
function createPaginationString(pagination: PaginationState) {
  if (!pagination) return "";
  const { pageIndex, pageSize } = pagination;
  return `${pageIndex}-${pageSize}`;
}

// takes a string like "0-10" and returns a PaginationState object
function parsePaginationString(paginationString: string): PaginationState {
  const [pageIndex, pageSize] = paginationString.split("-");
  if (!pageIndex || !pageSize) return DEFAULT_PAGINATION;
  if (isNaN(Number(pageIndex)) || isNaN(Number(pageSize)))
    return DEFAULT_PAGINATION;
  return { pageIndex: Number(pageIndex), pageSize: Number(pageSize) };
}
