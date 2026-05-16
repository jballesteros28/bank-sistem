import { useQuery } from "@tanstack/react-query";

import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";
import { useAuth } from "../../shared/hooks/useAuth";

export const brandingQueryKeys = {
  all: ["organizacion", "branding"],
  current: (token = "current") => ["organizacion", "branding", token || "current"],
};

export function getBrandingActual() {
  return httpClient.get(endpoints.organizacion.brandingActual);
}

export function updateBranding(payload) {
  return httpClient.patch(endpoints.organizacion.brandingActual, payload);
}

export function useBranding({ enabled = true } = {}) {
  const { token } = useAuth();

  return useQuery({
    queryKey: brandingQueryKeys.current(token),
    queryFn: getBrandingActual,
    enabled: Boolean(token) && enabled,
    retry: false,
    staleTime: 5 * 60_000,
  });
}
