// To parse this data:
//
//   import { Convert, IRecordResponse } from "./file";
//
//   const iRecordResponse = Convert.toIRecordResponse(json);
//
// These functions will throw an error if the JSON doesn't
// match the expected interface, even if the JSON is valid.

export interface Config {
  transitional: Transitional;
  adapter: string[];
  transformRequest: null[];
  transformResponse: null[];
  timeout: number;
  xsrfCookieName: string;
  xsrfHeaderName: string;
  maxContentLength: number;
  maxBodyLength: number;
  env: Request;
  headers: ConfigHeaders;
  baseURL: string;
  withCredentials: boolean;
  method: string;
  url: string;
  data: string;
}

export type Request = object;

export interface ConfigHeaders {
  Accept: string;
  "Content-Type": string;
  "X-Requested-By": string;
}

export interface Transitional {
  silentJSONParsing: boolean;
  forcedJSONParsing: boolean;
  clarifyTimeoutError: boolean;
}

export interface IRecordResponse {
  contents: Content[];
}

export interface Content {
  available_data_row_count: number;
  column_names: string[];
  data_rows: Array<DataRow[]>;
  record_offset: number;
  record_size: number;
  returned_data_row_count: number;
  sampling_ratio: number;
}

export type DataRow = number | null | string;

export interface IRecordResponseHeaders {
  "cache-control": string;
  "content-type": string;
  pragma: string;
}
