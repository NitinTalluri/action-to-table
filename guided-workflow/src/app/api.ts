import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/",
});
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("jwt");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
      return config;
    } else {
      config.headers["Authorization"] = null;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

export default client;

export const V2_URL = "/api/v2";
export const V2_WORKFLOW_URL = `${V2_URL}/workflows`;
