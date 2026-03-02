import axios from "axios";

import { clearAuth } from "@/lib/auth";
import { getIdToken, signOutUser } from "@/lib/firebaseAuth";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 45000,
});

api.interceptors.request.use(async (config) => {
  const token = await getIdToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      try {
        await signOutUser();
      } catch {
        // Ignore sign-out errors and clear local auth state.
      }
      clearAuth("session-expired");
    }
    return Promise.reject(error);
  }
);

export default api;
