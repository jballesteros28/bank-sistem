import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function listApiKeys(params) {
  return httpClient.get(endpoints.integraciones.apiKeys, { params });
}

export function listWebhooks(params) {
  return httpClient.get(endpoints.integraciones.webhooks, { params });
}

export function listWebhookDeliveries(params) {
  return httpClient.get(endpoints.integraciones.webhookDeliveries, { params });
}
