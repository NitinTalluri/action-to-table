import { getDcTypes } from "~/api/dcTypes";
import { dcTypesQueryKeys } from "~/utils/queryKeys";

export const getDcTypesQuery = {
  queryKey: dcTypesQueryKeys.lists(),
  queryFn: getDcTypes,
};
