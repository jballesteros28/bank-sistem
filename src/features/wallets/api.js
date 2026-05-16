import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const walletQueryKeys = {
  all: ["wallets"],
  user: (organizationId = "current") => ["wallets", "user", organizationId || "current"],
  organization: (organizationId = "current") => ["wallets", "organization", organizationId || "current"],
  organizationPrincipal: (organizationId = "current") => [
    "wallets",
    "organization",
    "principal",
    organizationId || "current",
  ],
};

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

export function createWalletOrganizacion(payload) {
  return httpClient.post(endpoints.wallets.organization, payload);
}
