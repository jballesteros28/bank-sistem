import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function getPlanActual() {
  return httpClient.get(endpoints.planes.actual);
}

export function listPlanes() {
  return httpClient.get(endpoints.planes.list);
}
