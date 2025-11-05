import {
  getContractsBooking,
  getContractsMonitor,
  getLinkableContracts,
} from "~/api/contracts";
import { contractsQueryKeys } from "~/utils/queryKeys";

export const contractsBookingQuery = (id: number) => ({
  queryKey: contractsQueryKeys.list(["booking", id]),
  queryFn: () => getContractsBooking(id),
});

export const contractsMonitorQuery = (id: number) => ({
  queryKey: contractsQueryKeys.list(["monitor", id]),
  queryFn: () => getContractsMonitor(id),
});

export const linkableContractsQuery = {
  queryKey: contractsQueryKeys.list("linkable"),
  queryFn: getLinkableContracts,
};
