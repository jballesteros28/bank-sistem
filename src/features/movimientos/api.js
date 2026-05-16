import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function listMovimientos(params) {
  return httpClient.get(endpoints.movimientos.list, { params });
}
