import client, { V2_URL } from "~/app/api";
import {
  BookingsContractResponseSchema,
  CreateMonitorContractResponseSchema,
  IBookingContractPost,
  IManagedContractBody,
  IMonitoredContract,
  LinkedContractResponseSchema,
  MonitoredContractsResponseSchema,
  parseBookingsContracts,
  parseLinkableContracts,
} from "~/domain/Contracts";

export const getLinkableContracts = async () => {
  const response = await client.get(`${V2_URL}/contracts/linkable/`);
  return parseLinkableContracts(response.data);
};

export const getContractsBooking = async (dcEngagementId: number) => {
  const response = await client.get(
    `${V2_URL}/contracts/booking/${dcEngagementId}`,
  );
  const data = await response.data;
  return parseBookingsContracts(data);
};

export const updateManagedContract = async (contract: IBookingContractPost) => {
  const response = await client.post(
    `${V2_URL}/contracts/managed/${contract.dc_engagement_id}`,
    contract,
  );
  return BookingsContractResponseSchema.parse(response.data);
};

export const createManagedContractLink = async (data: IManagedContractBody) => {
  const response = await client.post(`${V2_URL}/contracts/linkable/`, data);
  return LinkedContractResponseSchema.parse(response.data);
};

export const getContractsMonitor = async (dcEngagementId: number) => {
  const response = await client.get(
    `${V2_URL}/contracts/monitor/${dcEngagementId}`,
  );
  return MonitoredContractsResponseSchema.parse(response.data);
};

export const createContractsMonitor = async ({
  engagementId,
  data,
}: {
  engagementId: number;
  data: IMonitoredContract;
}) => {
  const response = await client.post(
    `${V2_URL}/contracts/monitor/${engagementId}`,
    data,
  );
  return CreateMonitorContractResponseSchema.parse(response.data);
};

export const deleteMonitorContract = async ({
  dc_engagement_id,
  contract_number,
}: {
  dc_engagement_id: number;
  contract_number: number;
}) => {
  const response = await client.delete(
    `${V2_URL}/contracts/monitor/${dc_engagement_id}/${contract_number}`,
  );
  return CreateMonitorContractResponseSchema.parse(response.data);
};

export const updateMonitorContract = async ({
  dc_engagement_id,
  data,
}: {
  dc_engagement_id: number;
  data: Partial<IMonitoredContract>;
}) => {
  const response = await client.put(
    `${V2_URL}/contracts/monitor/${dc_engagement_id}`,
    data,
  );
  return CreateMonitorContractResponseSchema.parse(response.data);
};
