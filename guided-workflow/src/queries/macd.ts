import { z } from "zod";

import {
  getMACDHistoricalSchemas,
  getMACDInputs,
  getMACDSchemas,
} from "~/api/macd";
import { TMACDInputResponse, TMACDToolSchemas } from "~/domain/MACD";
import { parseToolSchema } from "~/utils/generateMACDSchema";
import {
  macdHistoricalQueryKeys,
  macdInputsQueryKeys,
  macdSchemasQueryKeys,
} from "~/utils/queryKeys";

export const getMACDSchemasQuery = () => ({
  queryKey: macdSchemasQueryKeys.list(),
  queryFn: () => getMACDSchemas(),
  select: (
    data: Awaited<ReturnType<typeof getMACDSchemas>>,
  ): TMACDToolSchemas => {
    try {
      const validatedData = data.map((schema) => parseToolSchema(schema));
      return validatedData;
    } catch (error) {
      if (error instanceof z.ZodError) {
        console.error("Validation Error:", error.errors);
      } else {
        console.error("API Error:", error);
      }
      throw error;
    }
  },
});

export const getMACDInputsQuery = (engagementID: number) => ({
  queryKey: macdInputsQueryKeys.list(engagementID),
  queryFn: () => getMACDInputs(engagementID),
  select: (
    data: Awaited<ReturnType<typeof getMACDInputs>>,
  ): TMACDInputResponse => {
    data.sort((a, b) => b.request_id - a.request_id);
    return data;
  },
});

export const getMACDHistoricalInputsQuery = () => ({
  queryKey: macdHistoricalQueryKeys.list(),
  queryFn: () => getMACDHistoricalSchemas(),
});
