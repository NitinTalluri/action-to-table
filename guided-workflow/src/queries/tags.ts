import { getDeletedTags } from "~/api/tags";
import { tagsQueryKeys } from "~/utils/queryKeys";

export const getDeletedTagsQuery = {
  queryKey: tagsQueryKeys.list("deleted"),
  queryFn: getDeletedTags,
};
