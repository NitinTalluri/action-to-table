import { AxiosError } from "axios";
import { ZodError } from "zod";

/**
 * Generate error message for failed API request
 */
export const getErrorMessage = (
  defaultMessage: string,
  error: Error,
): string => {
  let message = defaultMessage;

  if (error instanceof AxiosError) {
    if (error.response?.data?.detail) {
      console.error(error.response);
      message = error.response.data.detail;
    }
  } else if (error instanceof ZodError) {
    console.error(error.issues);
    message =
      "Encountered issue with data validation. Data is not in expected format.";
  }
  return truncateMessage(message);
};

const truncateMessage = (message: string, maxLength = 100): string => {
  return message.length > maxLength
    ? message.slice(0, maxLength - 3) + "..."
    : message;
};
