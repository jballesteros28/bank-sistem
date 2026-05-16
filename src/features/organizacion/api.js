import { useQuery } from "@tanstack/react-query";

import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export function getBrandingActual() {
  return httpClient.get(endpoints.organizacion.brandingActual);
}

export function useBranding() {
  return useQuery({
    queryKey: ["organizacion", "branding"],
    queryFn: getBrandingActual,
    retry: false,
  });
}
