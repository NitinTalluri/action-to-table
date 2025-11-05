import {
  getDeletedEngagements,
  getEngagementOwners,
  getEngagements,
  getEngagementsUsers,
} from "~/api/engagements";
import {
  engagementOwnersQueryKeys,
  engagementsQueryKeys,
  engagementsUsersQueryKeys,
} from "~/utils/queryKeys";

export const getEngagementsUsersQuery = {
  queryKey: engagementsUsersQueryKeys.lists(),
  queryFn: getEngagementsUsers,
  staleTime: 3600000, // 1 hour this almost never changes
};

export const getEngagementsQuery = {
  queryKey: engagementsQueryKeys.lists(),
  queryFn: getEngagements,
};

export const getEngagementOwnersQuery = (engagementId: number) => ({
  queryKey: engagementOwnersQueryKeys.list(engagementId),
  queryFn: () => getEngagementOwners(engagementId),
});

export const getDeletedEngagementsQuery = {
  queryKey: engagementsQueryKeys.list("deleted"),
  queryFn: () => getDeletedEngagements(),
};
