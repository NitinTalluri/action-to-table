import { useMutation, useQueryClient } from "@tanstack/react-query";
import { DateTime } from "luxon";
import { toast } from "sonner";

import {
  getTimeTrackingEntries,
  getTimeTrackingWeeklyView,
  postTimeTrackingEntries,
} from "~/api/time-tracking";
import {
  TTimeTrackingEntryResponse,
  TTimeTrackingRow,
} from "~/domain/TimeTracking";
import {
  timeTrackingQueryKeys,
  timeTrackingSummaryQueryKeys,
} from "~/utils/queryKeys";

export const timeTrackingWeeklyViewQuery = (
  currentDate: string,
  nWeeks: number,
) => ({
  queryKey: timeTrackingSummaryQueryKeys.list(currentDate, nWeeks),
  queryFn: () => getTimeTrackingWeeklyView(currentDate, nWeeks),
  select: (data: Awaited<ReturnType<typeof getTimeTrackingWeeklyView>>) => {
    // Sort by week num
    return data.sort((a, b) => a.week_num_in_year - b.week_num_in_year);
  },
  staleTime: 1000 * 60 * 60, // 1 hour
});

export const timeTrackingQuery = (startDate: string, endDate: string) => ({
  queryKey: timeTrackingQueryKeys.list(startDate, endDate),
  queryFn: () => getTimeTrackingEntries(startDate, endDate),
  select: (data: TTimeTrackingEntryResponse) => {
    const groupedData = data.entries.reduce(
      (groupedData, entry) => {
        const {
          entry_id,
          dc_user_id,
          booking_contract,
          abstract_deliverable_id,
          deliverable_desc,
          entry_date,
          hours,
          week_num_in_year,
          fiscal_year_number,
          quarter,
          is_abstract,
        } = entry;

        const dc_engagement_id = entry.dc_engagement_id ?? -1;
        const deliverable_id =
          entry.deliverable_id ?? abstract_deliverable_id ?? -1;
        const engagement_name = entry.engagement_name ?? "Standard";

        const key = [dc_engagement_id, week_num_in_year].join("_");

        const engagementData = groupedData[key] || {
          id: dc_engagement_id,
          desc: engagement_name,
          deliverables: {},
          hours: {},

          entry_id: {},
          booking_contract: [booking_contract],
          dc_engagement_id,
          dc_user_id,
          fiscal_year_number,
          quarter,
          week_num_in_year,
          is_abstract,
          deliverable_id: null,
          abstract_deliverable_id: null,
        };

        const deliverableData = engagementData.deliverables[deliverable_id] || {
          id: deliverable_id,
          desc: deliverable_desc,
          hours: {},

          entry_id: {},
          booking_contract: [booking_contract],
          dc_engagement_id,
          dc_user_id,
          fiscal_year_number,
          quarter,
          week_num_in_year,
          is_abstract,
          deliverable_id,
          abstract_deliverable_id,
        };

        deliverableData.hours[entry_date] =
          (deliverableData.hours[entry_date] || 0) + hours;
        engagementData.hours[entry_date] =
          (engagementData.hours[entry_date] || 0) + hours;

        const entry_id_key = `${booking_contract}_${entry_date}`;
        deliverableData.entry_id[entry_id_key] = entry_id;

        if (!deliverableData.booking_contract.includes(booking_contract)) {
          deliverableData.booking_contract.push(booking_contract);
        }

        if (!engagementData.booking_contract.includes(booking_contract)) {
          engagementData.booking_contract.push(booking_contract);
        }

        engagementData.deliverables[deliverable_id] = deliverableData;
        groupedData[key] = engagementData;

        return groupedData;
      },
      {} as Record<string, TTimeTrackingRow>,
    );

    const flattenedGroupedData = Object.entries(groupedData).map(
      ([, engagementData]) => {
        return {
          ...engagementData,
          deliverables: Object.values(engagementData.deliverables).sort(
            (a, b) => b.id - a.id,
          ),
        };
      },
    );

    flattenedGroupedData.sort((a, b) => b.id - a.id);

    return flattenedGroupedData;
  },
});

export const useMutateCellData = (startDate: string, endDate: string) => {
  const currentDate = DateTime.local().toISODate();

  const queryClient = useQueryClient();
  const queryKey = timeTrackingQueryKeys.list(startDate, endDate);
  const weekSummaryQuery = timeTrackingSummaryQueryKeys.list(currentDate, 2);

  const { mutateAsync: updateTaskStatusMutation, isPending: isPendingUpdate } =
    useMutation({
      mutationFn: postTimeTrackingEntries,
      onSettled: async () => {
        await queryClient.invalidateQueries({
          queryKey: weekSummaryQuery,
        });
        await queryClient.invalidateQueries({
          queryKey,
        });
      },
    });

  const onUpdateTableEntries = (entries: TTimeTrackingRow[]) => {
    toast.promise(updateTaskStatusMutation(entries), {
      loading: "Updating data...",
      success: "Data updated successfully",
      error: "Failed to update Data",
    });
  };

  return { onUpdateTableEntries, isPendingUpdate };
};
