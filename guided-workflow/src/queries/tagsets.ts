import { getDeletedTagsets, getGlobalTagsets, getTagsets } from "~/api/tagset";
import { tagsetsQueryKeys } from "~/utils/queryKeys";

export const getTagsetsQuery = (engagementId: number) => ({
  queryKey: tagsetsQueryKeys.list(engagementId),
  queryFn: () => getTagsets(engagementId),
  enabled: typeof engagementId === "number",
  // 15 minutes
  staleTime: 15 * 60 * 1000,
  refetchOnWindowFocus: false,
});

export const getDeletedTagsetsQuery = {
  queryKey: tagsetsQueryKeys.list("deleted"),
  queryFn: getDeletedTagsets,
};

export const getGlobalTagsetsQuery = {
  queryKey: tagsetsQueryKeys.list(1),
  queryFn: getGlobalTagsets,
  // 15 minutes
  staleTime: 15 * 60 * 1000,
  refetchOnWindowFocus: false,
};
