import axios from "axios";

export const tsClient = axios.create({
  baseURL:
    import.meta.env.VITE_THOUGHTSPOT_HOST?.replace(/\/$/, "") +
      "/api/rest/2.0" || import.meta.env.VITE_THOUGHTSPOT_HOST,
  headers: {
    "X-Requested-By": "ThoughtSpot",
  },
  withCredentials: true,
});
