import { AxiosError } from "axios";
import { ZodError } from "zod";

export const serializeError = (error: unknown): string => {
  /**
   * When we catch errors from that we want to display, we need to:
   *  1. Assert the error is an Error object (typescript assumes it's unknown)
   *  2. Determine if it is AxiosError (from axios) or a native Error
   *  3. If it is an AxiosError, we need to extract the error message and code from the response
   * 4. If it is a ZodError, we need to extract the error message
   *  5. If it is a native Error, we need to extract the error message
   */

  if (!(error instanceof Error)) {
    console.error("Error is not an instance of Error", error);
    return "Unknown Error";
  }
  if (error instanceof AxiosError) {
    console.error(error.toJSON());
    if (error.response) {
      // https://axios-http.com/docs/handling_errors
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const { status, statusText } = error.response;
      return `Network Error ${status}: (${statusText})`;
    } else if (error.request) {
      // The request was made but no response was received
      return "Network Error: Unable to reach server";
    } else {
      // Something happened in setting up the request that triggered an Error
      return `Network Error: ${error.message}`;
    }
  } else if (error instanceof ZodError) {
    console.groupCollapsed("Parsing Error");
    console.table(error.issues);
    console.groupEnd();
    return `Parsing Error - Open console for more details`;
  } else {
    console.error(error);
    return `${error.name}: ${error.message}`;
  }
};
