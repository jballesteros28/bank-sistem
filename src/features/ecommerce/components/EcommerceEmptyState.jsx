import { ShoppingBag } from "lucide-react";

import { EmptyState } from "../../../shared/components/ui/EmptyState";

export function EcommerceEmptyState({
  title = "Todavia no hay ordenes ecommerce",
  description = "Cuando una tienda externa informe una compra pagada, el evento va a aparecer aca con su procesamiento.",
}) {
  return <EmptyState icon={ShoppingBag} title={title} description={description} />;
}
