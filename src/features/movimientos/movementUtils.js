export const movementTypeOptions = [
  { value: "deposito", label: "Deposito" },
  { value: "retiro", label: "Retiro" },
  { value: "transferencia", label: "Transferencia" },
  { value: "pago", label: "Pago" },
  { value: "pago_organizacion", label: "Pago organizacion" },
  { value: "cashback", label: "Cashback" },
  { value: "ajuste_admin", label: "Ajuste admin" },
  { value: "reversa", label: "Reversa" },
];

export const movementStatusOptions = [
  { value: "pendiente", label: "Pendiente" },
  { value: "aprobada", label: "Aprobada" },
  { value: "rechazada", label: "Rechazada" },
  { value: "cancelada", label: "Cancelada" },
  { value: "revertida", label: "Revertida" },
];

export function getMovementKind(movement) {
  if (movement?.tipo === "pago" && movement?.metadata?.operacion === "pago_organizacion") {
    return "pago_organizacion";
  }
  return movement?.tipo || "";
}

export function getMovementTypeLabel(value) {
  return movementTypeOptions.find((option) => option.value === value)?.label || value || "-";
}

export function getMovementStatusLabel(value) {
  return movementStatusOptions.find((option) => option.value === value)?.label || value || "-";
}

export function walletDisplayName(wallet) {
  if (!wallet) {
    return "-";
  }
  return wallet.alias || `${wallet.owner_type || "wallet"} ${String(wallet.id).slice(0, 8)}`;
}

export function createWalletMap(wallets = []) {
  return new Map(wallets.map((wallet) => [wallet.id, wallet]));
}

export function getWalletLabel(walletId, walletMap) {
  if (!walletId) {
    return "-";
  }
  const wallet = walletMap.get(walletId);
  return wallet ? walletDisplayName(wallet) : String(walletId).slice(0, 8);
}
