import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function listWallets(params) {
  return httpClient.get(endpoints.wallets.list, { params });
}

export function listOrganizationWallets(params) {
  return httpClient.get(endpoints.wallets.organization, { params });
}

export function getWalletsUsuario(params) {
  return listWallets(params);
}

export function getWalletsOrganizacion(params) {
  return listOrganizationWallets(params);
}

export function getWalletPrincipalOrganizacion(params) {
  return httpClient.get(endpoints.wallets.organizationPrincipal, { params });
}
