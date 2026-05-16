export function formatCurrency(value, currency = "ARS") {
  const numericValue = toNumber(value);
  const normalizedCurrency = currency || "ARS";

  try {
    return new Intl.NumberFormat("es-AR", {
      style: "currency",
      currency: normalizedCurrency,
      maximumFractionDigits: 2,
    }).format(numericValue);
  } catch {
    return `${formatNumber(numericValue)} ${normalizedCurrency}`;
  }
}

function toNumber(value) {
  if (value === null || value === undefined || value === "") {
    return 0;
  }
  const normalized = typeof value === "string" ? value.replace(",", ".") : value;
  const number = Number(normalized);
  return Number.isFinite(number) ? number : 0;
}

export function formatNumber(value) {
  return new Intl.NumberFormat("es-AR", {
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

export function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "medium",
  }).format(new Date(value));
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

export function formatLimit(value) {
  if (value === null || value === undefined) {
    return "Ilimitado";
  }
  return formatNumber(value);
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
