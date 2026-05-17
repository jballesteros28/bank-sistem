import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const ecommerceQueryKeys = {
  all: ["ecommerce"],
  orders: (organizationId = "current", params = {}) => ["ecommerce", "orders", organizationId || "current", params],
  order: (eventId) => ["ecommerce", "orders", eventId],
};

export function getEcommerceOrders(params) {
  return httpClient.get(endpoints.ecommerce.orders, { params });
}

export function getEcommerceOrderById(eventId) {
  return httpClient.get(endpoints.ecommerce.order(eventId));
}
