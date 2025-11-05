import axios, { AxiosError } from "axios";

export const isNotAuthenticatedError = (
  error: unknown,
): error is AxiosError<{ detail: string }> => {
  if (!axios.isAxiosError(error)) return false;
  const response = error.response;
  if (!response || response.status !== 403) return false;
  const data = response.data;
  if (!data) return false;
  return data.detail === "Not authenticated";
};
