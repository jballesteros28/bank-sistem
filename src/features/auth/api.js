import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function login(payload) {
  return httpClient.post(endpoints.auth.login, payload);
}

export function getCurrentUser() {
  return httpClient.get(endpoints.auth.me);
}
