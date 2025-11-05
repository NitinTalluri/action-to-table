import { getEngagementLinks } from "~/api/links";
import { engagementLinksQueryKeys } from "~/utils/queryKeys";

export const engagementLinksQuery = (engagementId: number) => ({
  queryKey: engagementLinksQueryKeys.list(engagementId),
  queryFn: () => getEngagementLinks(engagementId),
  // staletime of 15 minutes
  staleTime: 1000 * 60 * 15,
});
