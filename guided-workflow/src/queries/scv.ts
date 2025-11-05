import { getSuperCustomers } from "~/api/scv";
import { TSuperCustomerListResponse } from "~/domain/SCV";
import { superCustomeViewQueryKeys } from "~/utils/queryKeys";

export const getSuperCustomersQuery = {
  queryKey: superCustomeViewQueryKeys.lists(),
  queryFn: getSuperCustomers,
  select: (
    data: Awaited<ReturnType<typeof getSuperCustomers>>,
  ): TSuperCustomerListResponse => {
    data.super_customers.sort(
      (a, b) => b.super_customer_id - a.super_customer_id,
    );
    return data;
  },
};
