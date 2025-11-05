import { useQueries, UseQueryResult } from "@tanstack/react-query";

import { TTagsetEngagement, TTagsetGlobal } from "~/domain/Tagset";
import { getGlobalTagsetsQuery, getTagsetsQuery } from "~/queries/tagsets";

type TResult = [
  UseQueryResult<TTagsetEngagement[]>,
  UseQueryResult<TTagsetGlobal[]>,
];

const combineResults = (results: TResult) => {
  const isLoading = results.some((result) => result.isLoading);
  const isError = results.some((result) => result.isError);
  const dataResults = results.map((result) => result.data);

  const dataReady = dataResults.every((data) => data !== undefined);

  return {
    data: dataReady ? dataResults.flat() : undefined,
    isLoading,
    isError,
  };
};

type TGetTagsetParams = {
  engagementId: number;
  globalTagsetsSelect?: (result: TTagsetGlobal[]) => TTagsetGlobal[];
};

export const useGetTagsetsQueries = (params: TGetTagsetParams) => {
  const { engagementId, globalTagsetsSelect } = params;
  return useQueries({
    queries: [
      getTagsetsQuery(engagementId),
      { ...getGlobalTagsetsQuery, select: globalTagsetsSelect },
    ],
    combine: combineResults,
  });
};
