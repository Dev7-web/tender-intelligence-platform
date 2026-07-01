import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

import {
  clearAuth,
  getRefreshToken,
  getToken,
  setRefreshToken,
  setToken,
} from "@/lib/auth";

// AUTH MIGRATION (Firebase -> central auth gateway):
// The request interceptor now attaches the stored gateway id_token (instead of
// calling Firebase getIdToken() on every request). On 401 we try a single
// refresh via /auth/refresh (deduped), then retry the original request; if that
// fails we clear auth. Mirrors main-dashboard's api/client.js behaviour.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 45000,
});

const isAuthEndpoint = (url?: string) =>
  !!url && (url.includes("/auth/login") || url.includes("/auth/refresh"));

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token && !isAuthEndpoint(config.url)) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Dedupe concurrent refreshes: parallel 401s share one refresh request.
let refreshPromise: Promise<boolean> | null = null;

const tryRefreshToken = (): Promise<boolean> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return Promise.resolve(false);

  if (!refreshPromise) {
    // Bare axios (no interceptors) to avoid recursion.
    refreshPromise = axios
      .post(`${BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
      .then((res) => {
        const data = res?.data || {};
        if (!data.id_token) return false;
        setToken(data.id_token);
        if (data.refresh_token) setRefreshToken(data.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error?.response?.status;
    const original = error?.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (status === 401 && original && !original._retry && !isAuthEndpoint(original.url)) {
      original._retry = true;
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        const token = getToken();
        if (token) {
          original.headers = original.headers || {};
          original.headers.Authorization = `Bearer ${token}`;
        }
        return api(original);
      }
      clearAuth("session-expired");
    }

    return Promise.reject(error);
  }
);

export default api;
