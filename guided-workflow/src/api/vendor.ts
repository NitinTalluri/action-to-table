import client, { V2_URL } from "~/app/api";
import {
  TCAMVendorAssignment,
  TVendorPortalDeliverableList,
  VendorPortalDeliverableListSchema,
} from "~/domain/Vendor";

export const getVendorPortalDeliverablesList = async (
  bookingContract: number,
): Promise<TVendorPortalDeliverableList> => {
  const response = await client.get(
    `${V2_URL}/manager/bookings/sdp/${bookingContract}`,
  );
  return VendorPortalDeliverableListSchema.parse(response.data);
};

export const updateVendorCAMAssignment = async (data: TCAMVendorAssignment) => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/sdp/${data.booking_contract}`,
    data,
  );

  return response.data;
};
