import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

function normalizeLoginResponse(response) {
  return {
    accessToken: response?.access_token || response?.accessToken,
    tokenType: response?.token_type || response?.tokenType || "bearer",
    user: response?.user || null,
  };
}

export async function login(payload) {
  const response = await httpClient.post(endpoints.auth.login, {
    email: payload.email,
    password: payload.password,
  });
  const session = normalizeLoginResponse(response);
  if (!session.accessToken) {
    throw new Error("El backend no devolvio un access_token valido.");
  }
  return session;
}

export function getCurrentUser() {
  return httpClient.get(endpoints.auth.me);
}
