import { Badge } from "../../../shared/components/ui/Badge";
import { Card, CardHeader } from "../../../shared/components/ui/Card";

const events = [
  "wallet.creada",
  "movimiento.creado",
  "movimiento.revertido",
  "pago_organizacion.creado",
  "recompensa.aplicada",
  "notificacion.creada",
  "organizacion.suspendida",
];

export function WebhooksGuide() {
  return (
    <Card>
      <CardHeader
        title="Webhooks"
        description="Los webhooks notifican eventos operativos a una URL externa. El plan debe permitir webhooks y cada endpoint define eventos y secret."
      />
      <div className="flex flex-wrap gap-2">
        {events.map((event) => (
          <Badge key={event} tone="info">
            {event}
          </Badge>
        ))}
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-600">
        Los errores de entrega quedan registrados como deliveries y pueden reintentarse desde Integraciones cuando el rol lo permite.
      </p>
    </Card>
  );
}
