import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import { IContractUser } from "~/domain/Contracts/ContractUsers";
import {
  DisengagementResponseSchema,
  IClaimedBookingModify,
  IClaimedBookingModifyCalculated,
  IModifyBookingUserAssignment,
  IReplaceUser,
  IVerifiedBookingModifyDcTypes,
  ManagerPortalClaimedBookingSchema,
  ManagerPortalEngagementResponseSchema,
  ManagerPortalUnclaimedBookingSchema,
  RenewableBookingsSchema,
  TAllocationRequest,
  TAttachedEngagement,
  TCreateBookingRequest,
  TDisengagement,
  TDisengagementResponse,
  TManagerPortalClaimBooking,
  TManagerPortalClaimedBooking,
  TManagerPortalContractScope,
  TManagerPortalEngagementResponse,
  TManagerPortalUnclaimedBooking,
  TModifyBookingCurrentSalesLevel,
  TRenewableBookings,
} from "~/domain/ManagerPortal";

export const getManagerPortalUnclaimedBookings = async (): Promise<
  TManagerPortalUnclaimedBooking[]
> => {
  const response = await client.get(`${V2_URL}/manager/bookings/unclaimed`);
  return z.array(ManagerPortalUnclaimedBookingSchema).parse(response.data);
};

export const getManagerPortalClaimedBookings = async (): Promise<
  TManagerPortalClaimedBooking[]
> => {
  const response = await client.get(`${V2_URL}/manager/bookings/claimed`);
  return z.array(ManagerPortalClaimedBookingSchema).parse(response.data);
};

export const putManagerPortalClaimUnclaimedBooking = async (
  booking: TManagerPortalClaimBooking,
): Promise<TManagerPortalUnclaimedBooking> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/claim/${booking.booking_contract}`,
    booking,
  );
  return ManagerPortalUnclaimedBookingSchema.parse(response.data);
};

export const attachManagerPortalBookingToEngagement = async (
  booking: TAttachedEngagement,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/engagements/${booking.booking_contract}/${booking.dc_engagement_id}`,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const updateManagerPortalClaimedBooking = async (
  booking: TManagerPortalClaimedBooking,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.put(
    `${V2_URL}/manager/bookings/assignments`,
    booking,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const disengageManagerPortalBooking = async (
  disengagement: TDisengagement,
): Promise<TDisengagementResponse> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/disengage/${disengagement.booking_contract}`,
    disengagement,
  );
  return DisengagementResponseSchema.parse(response.data);
};

export const updateClaimedBooking = async (
  booking: IClaimedBookingModify,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.patch(
    `${V2_URL}/manager/bookings/claimed/${booking.booking_contract}`,
    booking,
  );

  return response.data;
};

export const updateClaimedBookingCalculation = async (
  booking: IClaimedBookingModifyCalculated,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.patch(
    `${V2_URL}/manager/bookings/claimed/${booking.booking_contract}/calculated`,
    booking,
  );

  return response.data;
};

export const updateClaimedBookingAssignments = async (
  booking: IModifyBookingUserAssignment,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.patch(
    `${V2_URL}/manager/bookings/claimed/${booking.booking_contract}/assignments`,
    booking,
  );
  return response.data;
};

export const updateVerifiedBookingDcTypes = async (
  booking: IVerifiedBookingModifyDcTypes,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.patch(
    `${V2_URL}/manager/bookings/claimed/${booking.booking_contract}/dc_types`,
    booking,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const updateCurrentSalesDetails = async (
  salesLevel: TModifyBookingCurrentSalesLevel,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/sales_levels`,
    { assignments: [salesLevel] },
  );
  return response.data;
};

export const getManagerPortalClaimedContracts = async (
  scope: TManagerPortalContractScope,
): Promise<Array<IContractUser>> => {
  const response = await client.get(`${V2_URL}/manager/users?scope=${scope}`);
  return response.data;
};

export const getManagerPortalRenewableBookings = async (): Promise<
  TRenewableBookings[]
> => {
  const response = await client.get(`${V2_URL}/manager/bookings/renewals`);
  return z.array(RenewableBookingsSchema).parse(response.data);
};

export const putManagerPortalBookingAssignments = async (
  data: IModifyBookingUserAssignment,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.put(
    `${V2_URL}/manager/bookings/assignments`,
    data,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const replaceManagerPortalUser = async (
  data: IReplaceUser,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/assignments/replace`,
    data,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const postManagerPortalExtendBookingContract = async (
  booking_contract: number,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/extend/${booking_contract}`,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const deleteManagerPortalUnclaimBooking = async (
  bookingContract: TManagerPortalClaimBooking["booking_contract"],
) => {
  const response = await client.delete(
    `${V2_URL}/manager/bookings/claim/${bookingContract}`,
  );
  return response.data;
};

export const patchManagerPortalAllocationRatio = async (
  ratios: TAllocationRequest,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.patch(
    `${V2_URL}/manager/bookings/claimed/${ratios.booking_contract}/allocation_ratio`,
    ratios,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const getManagerPortalAvailableEngagements = async (): Promise<
  TManagerPortalEngagementResponse[]
> => {
  const response = await client.get(`${V2_URL}/manager/bookings/engagements`);
  return z.array(ManagerPortalEngagementResponseSchema).parse(response.data);
};

export const createManagerPortalProspectingBooking = async (
  booking: TCreateBookingRequest,
): Promise<TManagerPortalClaimedBooking> => {
  const response = await client.post(
    `${V2_URL}/manager/bookings/prospective`,
    booking,
  );
  return ManagerPortalClaimedBookingSchema.parse(response.data);
};

export const deleteManagerPortalProspectingBooking = async (
  bookingContract: number,
) => {
  const response = await client.delete(
    `${V2_URL}/manager/bookings/prospective/${bookingContract}`,
  );
  return response.data;
};

