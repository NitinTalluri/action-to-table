import client, { V2_URL } from "~/app/api";
import {
  TimeTrackingEntryResponseSchema,
  TimeTrackingPrecision,
  TimeTrackingWeeklyViewResponseSchema,
  TTimeTrackingPayloadList,
  TTimeTrackingPayloadRequest,
  TTimeTrackingRow,
} from "~/domain/TimeTracking";

const largestRemainder = (
  total: number,
  n_parts: number,
  precision: number = 3,
) => {
  /*

  This function takes a total number and divides it into n_parts, distributing the remainder
  as evenly as possible across the parts. It returns an array of numbers representing the
  distributed values.

  largestRemainder(8, 3, 3) = [2.667, 2.667, 2.666]

  */
  const scale = Math.pow(10, precision);
  const totalScaled = Math.round(total * scale);
  const intPart = Math.floor(totalScaled / n_parts);
  const remainder = totalScaled % n_parts;

  const result = Array(n_parts).fill(intPart);

  for (let i = 0; i < remainder; i++) {
    result[i]++;
  }

  return result.map<number>((r) => +(r / scale).toFixed(precision));
};

const flattenTimeTrackingData = (data: TTimeTrackingRow[]) => {
  return {
    entries: data.flatMap((engagement) =>
      engagement.deliverables.flatMap((deliverable) =>
        Object.entries(deliverable.hours).flatMap(([date, hours]) => {
          const rows: TTimeTrackingPayloadList = [];

          if (deliverable.is_abstract && deliverable.abstract_deliverable_id) {
            const entry_id = deliverable.entry_id[`null_${date}`] || null;

            rows.push({
              entry_id,
              booking_contract: null,
              dc_engagement_id: null,
              dc_user_id: deliverable.dc_user_id,
              deliverable_id: null,
              abstract_deliverable_id: deliverable.abstract_deliverable_id,
              entry_date: date,
              hours: hours,
              is_abstract: true,
            });
          } else {
            const booking_contracts = deliverable.booking_contract;
            const perContractHour = largestRemainder(
              hours,
              booking_contracts.length,
              TimeTrackingPrecision,
            );

            booking_contracts.forEach((b, i) => {
              if (b && deliverable.deliverable_id) {
                const entry_id_key = `${b}_${date}`;
                const entry_id = deliverable.entry_id[entry_id_key] || null;

                rows.push({
                  entry_id,
                  booking_contract: b,
                  dc_engagement_id: deliverable.dc_engagement_id,
                  dc_user_id: deliverable.dc_user_id,
                  deliverable_id: deliverable.deliverable_id,
                  abstract_deliverable_id: null,
                  entry_date: date,
                  hours: perContractHour[i],
                  is_abstract: false,
                });
              }
            });
          }

          return rows;
        }),
      ),
    ),
  };
};

export const getTimeTrackingWeeklyView = async (
  currentDate: string,
  nWeeks: number,
) => {
  const response = await client.get(`${V2_URL}/sdp/time_tracking/weekly`, {
    params: {
      date: currentDate,
      n_weeks: nWeeks,
    },
  });

  return TimeTrackingWeeklyViewResponseSchema.parse(response.data);
};

export const getTimeTrackingEntries = async (
  startDate: string,
  endDate: string,
) => {
  const response = await client.get(`${V2_URL}/sdp/time_tracking`, {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });
  return TimeTrackingEntryResponseSchema.parse(response.data);
};

export const postTimeTrackingEntries = async (data: TTimeTrackingRow[]) => {
  const flattenedData: TTimeTrackingPayloadRequest =
    flattenTimeTrackingData(data);

  const response = await client.post(
    `${V2_URL}/sdp/time_tracking `,
    flattenedData,
  );

  return TimeTrackingEntryResponseSchema.parse(response.data);
};
