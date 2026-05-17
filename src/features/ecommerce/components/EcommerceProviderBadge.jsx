import { Badge } from "../../../shared/components/ui/Badge";
import { getProviderLabel } from "../schemas";

const providerTones = {
  generic: "neutral",
  tienda_nube: "info",
  shopify: "success",
  woocommerce: "warning",
  mercado_pago: "info",
};

export function EcommerceProviderBadge({ provider }) {
  return <Badge tone={providerTones[provider] || "neutral"}>{getProviderLabel(provider)}</Badge>;
}
