import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function listNotificaciones(params) {
  return httpClient.get(endpoints.notificaciones.list, { params });
}

export function getUnreadNotificationsCount() {
  return httpClient.get(endpoints.notificaciones.unreadCount);
}
