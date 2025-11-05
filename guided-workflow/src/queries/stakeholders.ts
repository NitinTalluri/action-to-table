import { getStakeholders } from "~/api/stakeholders";
import { stakeholdersQueryKeys } from "~/utils/queryKeys";

export const stakeholdersQuery = (id: number) => ({
  queryKey: stakeholdersQueryKeys.list(id),
  queryFn: () => getStakeholders(id),
});
