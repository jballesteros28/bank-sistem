import axios from "axios";

import { useAuthStore } from "../../features/auth/store";
import { getToken } from "../utils/storage";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
const apiPrefix = import.meta.env.VITE_API_PREFIX || "/api/v1";

function joinUrl(baseUrl, prefix) {
  return `${baseUrl.replace(/\/$/, "")}/${prefix.replace(/^\//, "")}`;
}

export const httpClient = axios.create({
  baseURL: joinUrl(apiBaseUrl, apiPrefix),
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => {
    const payload = response.data;
    if (payload && typeof payload === "object" && "success" in payload && "data" in payload) {
      return payload.data;
    }
    return payload;
  },
  (error) => {
    if (error?.response?.status === 401) {
      useAuthStore.getState().logout({ redirect: false });
      if (!window.location.pathname.startsWith("/login")) {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);
