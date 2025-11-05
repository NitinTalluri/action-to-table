import { getVendorPortalDeliverablesList } from "~/api/vendor";
import { vendorPortalDeliverablesListQueryKeys } from "~/utils/queryKeys";

export const vendorPortalDeliverablesListQuery = (bookingContract: number) => ({
  queryKey: vendorPortalDeliverablesListQueryKeys.list(bookingContract),
  queryFn: () => getVendorPortalDeliverablesList(bookingContract),
});
