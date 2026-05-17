export const ECOMMERCE_PROVIDERS = [
  { value: "generic", label: "Generic" },
  { value: "tienda_nube", label: "Tienda Nube" },
  { value: "shopify", label: "Shopify" },
  { value: "woocommerce", label: "WooCommerce" },
  { value: "mercado_pago", label: "Mercado Pago" },
];

export const ECOMMERCE_STATUSES = [
  { value: "paid", label: "Pagada" },
  { value: "cancelled", label: "Cancelada" },
  { value: "refunded", label: "Reembolsada" },
];

export const PROCESSING_STATES = [
  { value: "procesado", label: "Procesado" },
  { value: "error", label: "Error" },
  { value: "pendiente", label: "Pendiente" },
];

export function getProviderLabel(provider) {
  return ECOMMERCE_PROVIDERS.find((option) => option.value === provider)?.label || provider || "-";
}

export function getStatusLabel(status) {
  return ECOMMERCE_STATUSES.find((option) => option.value === status)?.label || status || "-";
}

export function getProcessingState(order) {
  if (order?.error_procesamiento) {
    return "error";
  }
  if (order?.procesado) {
    return "procesado";
  }
  return "pendiente";
}
