import { z } from "zod";

export const TimeTrackingPrecision = 2;

// Zod Schemas
export const TimeTrackingWeekViewSchemaBase = z.object({
  start_date: z.string(),
  end_date: z.string(),
  fiscal_year_number: z.number(),
  quarter: z.number(),
  week_num_in_year: z.number(),
  year: z.number(),
  total_hours: z.coerce.number(),
});

type TTimeTrackingWeekViewBase = z.infer<typeof TimeTrackingWeekViewSchemaBase>;

export type TWeekYear = `W${number}-Y${number}`;

export const getWeekYearKey = (week: number, year: number): TWeekYear => {
  return `W${week}-Y${year}`;
};

export const TimeTrackingWeekViewSchema =
  TimeTrackingWeekViewSchemaBase.transform<
    TTimeTrackingWeekViewBase & { week_year: TWeekYear }
  >((data) => {
    const { week_num_in_year, year } = data;
    const week_year = getWeekYearKey(week_num_in_year, year);
    return {
      ...data,
      week_year,
    };
  });

export const TimeTrackingConcreteEntrySchema = z.object({
  entry_id: z.number().nullable(),
  booking_contract: z.number(),
  dc_engagement_id: z.number(),
  engagement_name: z.string(),
  dc_user_id: z.number(),
  deliverable_desc: z.string(),
  deliverable_id: z.number(),
  abstract_deliverable_id: z.null(),
  entry_date: z.string(),
  fiscal_year_number: z.number(),
  hours: z.number(),
  is_abstract: z.literal(false),
  quarter: z.number(),
  week_num_in_year: z.number(),
});

export const TimeTrackingAbstractEntrySchema = z.object({
  entry_id: z.number().nullable(),
  booking_contract: z.null(),
  dc_engagement_id: z.null(),
  engagement_name: z.null(),
  dc_user_id: z.number(),
  deliverable_desc: z.string(),
  deliverable_id: z.null(),
  abstract_deliverable_id: z.number(),
  entry_date: z.string(),
  fiscal_year_number: z.number(),
  hours: z.number(),
  is_abstract: z.literal(true),
  quarter: z.number(),
  week_num_in_year: z.number(),
});

export const TimeTrackingAbstractPayloadSchema = z.object({
  entry_id: z.number().nullable(),
  booking_contract: z.null(),
  dc_engagement_id: z.null(),
  dc_user_id: z.number(),
  deliverable_id: z.null(),
  abstract_deliverable_id: z.number(),
  entry_date: z.string(),
  hours: z.number(),
  is_abstract: z.literal(true),
});

export const TimeTrackingConcretePayloadSchema = z.object({
  entry_id: z.number().nullable(),
  booking_contract: z.number(),
  dc_engagement_id: z.number(),
  dc_user_id: z.number(),
  deliverable_id: z.number(),
  abstract_deliverable_id: z.null(),
  entry_date: z.string(),
  hours: z.number(),
  is_abstract: z.literal(false),
});

export const TimeTrackingPayloadSchema = z.discriminatedUnion("is_abstract", [
  TimeTrackingAbstractPayloadSchema,
  TimeTrackingConcretePayloadSchema,
]);

export const TimeTrackingEntrySchema = z.discriminatedUnion("is_abstract", [
  TimeTrackingConcreteEntrySchema,
  TimeTrackingAbstractEntrySchema,
]);

export const TimeTrackingEntriesListSchema = z.array(TimeTrackingEntrySchema);
export const TimeTrackingPayloadListSchema = z.array(TimeTrackingPayloadSchema);

export const TimeTrackingEntryResponseSchema = z.object({
  entries: TimeTrackingEntriesListSchema,
});
export const TimeTrackingPayloadRequestSchema = z.object({
  entries: TimeTrackingPayloadListSchema,
});

export const TimeTrackingWeeklyViewResponseSchema = z.array(
  TimeTrackingWeekViewSchema,
);

// TypeScript Types
export type TTimeTrackingWeekView = z.infer<typeof TimeTrackingWeekViewSchema>;

export type TTimeTrackingConcreteEntry = z.infer<
  typeof TimeTrackingConcreteEntrySchema
>;
export type TTimeTrackingAbstractEntry = z.infer<
  typeof TimeTrackingAbstractEntrySchema
>;
export type TTimeTrackingAbstractPayload = z.infer<
  typeof TimeTrackingAbstractPayloadSchema
>;
export type TTimeTrackingConcretePayload = z.infer<
  typeof TimeTrackingConcretePayloadSchema
>;

export type TTimeTrackingEntry = z.infer<typeof TimeTrackingEntrySchema>;
export type TTimeTrackingPayload = z.infer<typeof TimeTrackingPayloadSchema>;

export type TTimeTrackingEntriesList = z.infer<
  typeof TimeTrackingEntriesListSchema
>;
export type TTimeTrackingPayloadList = z.infer<
  typeof TimeTrackingPayloadListSchema
>;

export type TTimeTrackingEntryResponse = z.infer<
  typeof TimeTrackingEntryResponseSchema
>;
export type TTimeTrackingPayloadRequest = z.infer<
  typeof TimeTrackingPayloadRequestSchema
>;

export type TTimeTrackingWeeklyViewResponse = z.infer<
  typeof TimeTrackingWeeklyViewResponseSchema
>;

export type TTimeTrackingRow = {
  id: number;
  desc: string;
  hours: Record<string, number>;
  deliverables: TTimeTrackingRow[];

  entry_id: Record<string, number | null>;
  booking_contract: [number | null];
  dc_engagement_id: number;
  dc_user_id: number;
  deliverable_id: number | null;
  abstract_deliverable_id: number | null;
  fiscal_year_number: number;
  is_abstract: boolean;
  quarter: number;
  week_num_in_year: number;
};
