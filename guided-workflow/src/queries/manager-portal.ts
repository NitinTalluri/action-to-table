import {
  getManagerPortalAvailableEngagements,
  getManagerPortalClaimedBookings,
  getManagerPortalClaimedContracts,
  getManagerPortalRenewableBookings,
  getManagerPortalUnclaimedBookings,
} from "~/api/manager-portal";
import { TManagerPortalContractScope } from "~/domain/ManagerPortal";
import {
  managerPortalAvailableEngagementsQueryKeys,
  managerPortalClaimedBookingsQueryKeys,
  managerPortalClaimedContractsQueryKeys,
  managerPortalRenewableBookingsQueryKeys,
  managerPortalUnclaimedBookingsQueryKeys,
} from "~/utils/queryKeys";

export const managerPortalUnclaimedBookingsQuery = {
  queryKey: managerPortalUnclaimedBookingsQueryKeys.lists(),
  queryFn: getManagerPortalUnclaimedBookings,
};

export const managerPortalClaimedBookingsQuery = {
  queryKey: managerPortalClaimedBookingsQueryKeys.lists(),
  queryFn: getManagerPortalClaimedBookings,
};

export const managerPortalClaimedContractsQuery = (
  scope: TManagerPortalContractScope,
) => ({
  queryKey: managerPortalClaimedContractsQueryKeys.list(scope),
  queryFn: () => getManagerPortalClaimedContracts(scope),
});

export const managerPortalRenewableBookingsQuery = {
  queryKey: managerPortalRenewableBookingsQueryKeys.lists(),
  queryFn: getManagerPortalRenewableBookings,
};

export const managerPortalAvailableEngagementsQuery = {
  queryKey: managerPortalAvailableEngagementsQueryKeys.lists(),
  queryFn: getManagerPortalAvailableEngagements,
};

