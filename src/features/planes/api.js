import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const planQueryKeys = {
  all: ["planes"],
  list: ["planes", "list"],
  current: (organizationId = "current") => ["planes", "actual", organizationId || "current"],
};

export function getPlanActual() {
  return httpClient.get(endpoints.planes.actual);
}

export function listPlanes() {
  return httpClient.get(endpoints.planes.list);
}

export function getPlanes() {
  return listPlanes();
}
