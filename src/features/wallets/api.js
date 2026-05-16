import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function listWallets(params) {
  return httpClient.get(endpoints.wallets.list, { params });
}

export function listOrganizationWallets(params) {
  return httpClient.get(endpoints.wallets.organization, { params });
}
