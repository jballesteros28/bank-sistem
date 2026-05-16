export const notificationTypeOptions = [
  { value: "onboarding_exitoso", label: "Onboarding" },
  { value: "wallet_creada", label: "Wallet creada" },
  { value: "wallet_organizacion_creada", label: "Wallet organizacion" },
  { value: "movimiento_deposito", label: "Deposito" },
  { value: "movimiento_retiro", label: "Retiro" },
  { value: "movimiento_transferencia", label: "Transferencia" },
  { value: "movimiento_pago", label: "Pago" },
  { value: "movimiento_cashback", label: "Cashback" },
  { value: "movimiento_ajuste_admin", label: "Ajuste admin" },
  { value: "movimiento_reversa", label: "Reversa" },
  { value: "pago_organizacion_realizado", label: "Pago realizado" },
  { value: "pago_organizacion_recibido", label: "Pago recibido" },
  { value: "wallet_congelada", label: "Wallet congelada" },
  { value: "organizacion_suspendida", label: "Organizacion suspendida" },
  { value: "seguridad", label: "Seguridad" },
];

export const notificationChannelOptions = [
  { value: "interna", label: "Interna" },
  { value: "email", label: "Email" },
];

export function getNotificationTypeLabel(value) {
  return notificationTypeOptions.find((option) => option.value === value)?.label || value || "-";
}

export function getNotificationChannelLabel(value) {
  return notificationChannelOptions.find((option) => option.value === value)?.label || value || "-";
}

export function normalizeNotificationList(response) {
  return {
    items: response?.items || [],
    total: response?.total || 0,
    noLeidas: response?.no_leidas || 0,
  };
}
