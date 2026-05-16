import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const integrationsQueryKeys = {
  all: ["integraciones"],
  apiKeys: (organizationId = "current") => ["integraciones", "api-keys", organizationId || "current"],
  webhooks: (organizationId = "current") => ["integraciones", "webhooks", organizationId || "current"],
  deliveries: (organizationId = "current", params = {}) => [
    "integraciones",
    "webhook-deliveries",
    organizationId || "current",
    params,
  ],
};

export function getApiKeys(params) {
  return httpClient.get(endpoints.integraciones.apiKeys, { params });
}

export function createApiKey(payload) {
  return httpClient.post(endpoints.integraciones.apiKeys, payload);
}

export function revokeApiKey(apiKeyId) {
  return httpClient.delete(`${endpoints.integraciones.apiKeys}/${apiKeyId}`);
}

export function getWebhooks(params) {
  return httpClient.get(endpoints.integraciones.webhooks, { params });
}

export function createWebhook(payload) {
  return httpClient.post(endpoints.integraciones.webhooks, payload);
}

export function updateWebhook(webhookId, payload) {
  return httpClient.patch(`${endpoints.integraciones.webhooks}/${webhookId}`, payload);
}

export function deleteWebhook(webhookId) {
  return httpClient.delete(`${endpoints.integraciones.webhooks}/${webhookId}`);
}

export function getWebhookDeliveries(params) {
  return httpClient.get(endpoints.integraciones.webhookDeliveries, { params });
}

export function retryWebhookDelivery(deliveryId) {
  return httpClient.post(endpoints.integraciones.reenviarDelivery(deliveryId));
}

export const listApiKeys = getApiKeys;
export const listWebhooks = getWebhooks;
export const listWebhookDeliveries = getWebhookDeliveries;
