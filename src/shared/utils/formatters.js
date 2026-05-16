export function formatCurrency(value, currency = "ARS") {
  const numericValue = Number(value || 0);
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(numericValue);
}

export function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function humanizeRole(role) {
  const labels = {
    super_admin: "Super admin",
    owner: "Owner",
    admin: "Admin",
    soporte: "Soporte",
    cliente: "Cliente",
  };
  return labels[role] || role || "-";
}
