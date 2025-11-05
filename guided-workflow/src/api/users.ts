import client, { V2_URL } from "~/app/api";

const FETCH_WHO_AM_I_KEY = "dc_user_id";

export const fetchWhoAmI = async (): Promise<number> => {
  const whoAmI = localStorage.getItem(FETCH_WHO_AM_I_KEY);
  if (whoAmI) {
    try {
      return parseInt(whoAmI);
    } catch (e) {
      console.error("Error parsing whoami from localStorage", e);
      localStorage.removeItem(FETCH_WHO_AM_I_KEY);
    }
  }

  const response = await client.get<number>(`${V2_URL}/users/whoami`);
  localStorage.setItem(FETCH_WHO_AM_I_KEY, response.data.toString());
  return response.data;
};

export const clearWhoAmI = async () => {
  localStorage.removeItem(FETCH_WHO_AM_I_KEY);
};
