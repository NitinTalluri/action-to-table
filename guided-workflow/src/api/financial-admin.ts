import { z } from "zod";

import client, { V2_URL } from "~/app/api";
import {
  IUnverifiedBookingResponse,
  IVerifyBooking,
  UnverifiedBookingResponseSchema,
} from "~/domain/admin/bookings/unverifiedBooking";
import {
  IModifyBookingUserAssignment,
  IVerifiedBookingModifyCalculated,
  IVerifiedBookingModifyDcTypes,
  IVerifiedBookingResponse,
  VerifiedBookingResponseSchema,
} from "~/domain/admin/bookings/verifiedBooking";
import { TMappedContractOutput } from "~/domain/admin/contracts/contracts";
import { TGridModel } from "~/features/financial-admin/revenue/useRevenueGrid";
import { TRevenueTab } from "~/features/financial-admin/revenue/useRevenueLocation";
import { TSeaGridsModel } from "~/features/financial-admin/sea/useSeaGrids";
import { TSEATab } from "~/features/financial-admin/sea/useTabLocation";

export const getUnverifiedBookings = async () => {
  const response = await client.get(
    `${V2_URL}/admin/financial/bookings/unverified`,
  );
  const data = await response.data;
  const parsedData = z.array(UnverifiedBookingResponseSchema).safeParse(data);
  if (!parsedData.success) {
    throw new Error("Failed to parse unverified bookings");
  }
  return parsedData.data;
};

export type TUnverifiedBookingResponse = Pick<
  IUnverifiedBookingResponse,
  "booking_contract"
>;

export const verifyUnverifiedBooking = async (
  booking: IVerifyBooking,
): Promise<TUnverifiedBookingResponse> => {
  const response = await client.post<TUnverifiedBookingResponse>(
    `${V2_URL}/admin/financial/bookings/unverified`,
    booking,
  );
  return response.data;
};

export const getVerifiedBookings = async (): Promise<
  IVerifiedBookingResponse[]
> => {
  const response = await client.get(
    `${V2_URL}/admin/financial/bookings/verified`,
  );
  const data = await response.data;
  return z.array(VerifiedBookingResponseSchema).parse(data);
};

export const updateVerifiedBookingCalculation = async (
  booking: IVerifiedBookingModifyCalculated,
): Promise<IVerifiedBookingResponse> => {
  const response = await client.patch(
    `${V2_URL}/admin/financial/bookings/verified/${booking.booking_contract}/calculated`,
    booking,
  );

  return response.data;
};

export const updateVerifiedBookingDcTypes = async (
  booking: IVerifiedBookingModifyDcTypes,
): Promise<IVerifiedBookingResponse> => {
  const response = await client.patch(
    `${V2_URL}/admin/financial/bookings/verified/${booking.booking_contract}/dc_types`,
    booking,
  );
  return VerifiedBookingResponseSchema.parse(response.data);
};

export const updateVerifiedBookingAssignments = async (
  booking: IModifyBookingUserAssignment,
): Promise<IVerifiedBookingResponse> => {
  const response = await client.patch(
    `${V2_URL}/admin/financial/bookings/verified/${booking.booking_contract}/assignments`,
    booking,
  );
  return response.data;
};

type TSubmitRevenueResponse = {
  count: number;
};

export const submitRevenueEntries = async <T extends TRevenueTab>(
  entries: TGridModel<T>,
  revenueType: T,
): Promise<TSubmitRevenueResponse> => {
  const response = await client.post<TSubmitRevenueResponse>(
    `${V2_URL}/admin/financial/revenue/${revenueType}`,
    entries,
  );
  return response.data;
};

/**
 * Calls a stored procedure - used by some downstream systems? This is parameterless, i.e. tab does not matter
 */
export const processRevenueEntries = async (): Promise<void> => {
  await client.post(`${V2_URL}/admin/financial/revenue/process`);
};

/**
 * Runs a truncate operation on the revenue table
 * @param revenueType
 */
export const clearRevenueEntries = async <T extends TRevenueTab>(
  revenueType: T,
): Promise<void> => {
  await client.post(`${V2_URL}/admin/financial/revenue/clear/${revenueType}`);
};

export const submitContractsEntries = async (
  entries: TMappedContractOutput[],
) => {
  const response = await client.post(
    `${V2_URL}/admin/financial/contracts`,
    entries,
  );
  return response.data;
};

type TSubmitSEAResponse = {
  count: number;
};

export const submitSEAEntries = async <T extends TSEATab>(
  entries: TSeaGridsModel<T>,
): Promise<TSubmitSEAResponse> => {
  const response = await client.post<TSubmitSEAResponse>(
    `${V2_URL}/admin/financial/revenue/sea`,
    entries,
  );
  return response.data;
};
