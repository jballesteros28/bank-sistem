import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function registerOrganization(payload) {
  return httpClient.post(endpoints.onboarding.registroOrganizacion, payload);
}
