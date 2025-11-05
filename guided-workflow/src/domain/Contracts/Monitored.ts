import { z } from "zod";

export const MonitoredContractSchema = z.object({
  contract_number: z.coerce.number().positive(),
  created_by: z.string().nullish(),
  monitor_notes: z.string().nullable(),
  monitor_reason: z.string().nullable(),
  monitor_type_id: z.number().positive(),
});

export const MonitoredContractsResponseSchema = z.array(
  MonitoredContractSchema,
);

export type IMonitoredContract = z.infer<typeof MonitoredContractSchema>;

export const parseMonitoredContract = (
  data: unknown,
): Promise<IMonitoredContract> => {
  return MonitoredContractSchema.parseAsync(data);
};

export const parseMonitoredContracts = (
  data: unknown,
): Promise<IMonitoredContract[]> => {
  return MonitoredContractsResponseSchema.parseAsync(data);
};
