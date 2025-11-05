import { z } from "zod";

export type TrueFalse = "T" | "F";
export type Booleanized<T> = {
  // Convert string "T" and "F" to boolean
  [P in keyof T]: T[P] extends TrueFalse ? boolean : T[P];
};

export interface Links {
  ACAT_CUSTOMER_ID?: number[];
  MCE_ENGAGEMENT_NUMBER?: number[];
  CR_PARTY_ID?: number[];
  SMART_ACCOUNT?: number[];
}

export interface Engagement {
  dc_engagement_id: number;
  engagement_name?: string;
  is_cxea?: boolean;
  is_sfc?: string;
  is_software?: string;
  notes?: string;
  sfc_agreement_type?: number;
}

export interface NewEngagement {
  engagement_name: string;
  is_cxea?: boolean;
  is_sfc?: string;
  is_software?: string;
  notes?: string;
  sfc_agreement_type?: number;
}

export interface TagSet {
  tagset_id?: number;
  tagset_name?: string;
  tagset_desc?: string;
  scope?: string;
  cardinality?: string;
  tagset_type?: number;
  dc_engagement_id?: number;
  tags?: Array<Tag>;
}

export interface Tag {
  tag_id?: number;
  tag_name?: string;
  tag_desc?: string;
  tagset_id?: number;
}

export interface Canvas {
  canvas_name: string;
  canvas_type: string;
  canvas_id: number;
  canvas_desc?: string;
  source_data_date_filter?: string;
  file_path?: string;
  file_upload_status?: string;
  canvas_status?: string;
  tag_actions?: number;
  extract_actions?: number;
  pinboards?: Array<Pinboard>;
  // created_dtm?: Date;
}

export interface Pinboard {
  pinboard_name?: string;
  dashboard_name?: string;
  link?: string;
}

export const DataSourceSchema = z.object({
  remote_system_customer_identifier: z.number(),
  file_name: z.string(),
  folder_path: z.string(),
  file_source: z.string(),
  file_type: z.string(),
  num_records: z.number(),
  date_sourced: z.string(),
  last_processed_date: z.string(),
  remote_system: z.string(),
  file_number: z.number(),
  display_name: z.string(),
  request_id: z.coerce.number(),
});

export type DataSource = z.infer<typeof DataSourceSchema>;

export interface ThoughtSpot {
  user: string;
  dashboard_name: string;
  pinboard_name: string;
  link: string;
  object_uuid: string;
}
