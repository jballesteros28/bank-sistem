import { Badge } from "../../../shared/components/ui/Badge";
import { getNotificationTypeLabel } from "../notificationUtils";

const tones = {
  onboarding_exitoso: "success",
  wallet_creada: "info",
  wallet_organizacion_creada: "info",
  movimiento_deposito: "success",
  movimiento_retiro: "warning",
  movimiento_transferencia: "info",
  movimiento_pago: "neutral",
  movimiento_cashback: "success",
  movimiento_ajuste_admin: "warning",
  movimiento_reversa: "danger",
  pago_organizacion_realizado: "info",
  pago_organizacion_recibido: "success",
  wallet_congelada: "danger",
  organizacion_suspendida: "danger",
  seguridad: "warning",
};

export function NotificationTypeBadge({ tipo }) {
  return <Badge tone={tones[tipo] || "neutral"}>{getNotificationTypeLabel(tipo)}</Badge>;
}
