export const endpoints = {
  auth: {
    login: "/auth/login",
    me: "/auth/me",
  },
  onboarding: {
    registroOrganizacion: "/onboarding/registro-organizacion",
  },
  dashboard: {
    resumen: "/admin/resumen",
  },
  wallets: {
    list: "/wallets",
    organization: "/wallets/organizacion",
    organizationPrincipal: "/wallets/organizacion/principal",
  },
  movimientos: {
    list: "/movimientos",
    detail: (movimientoId) => `/movimientos/${movimientoId}`,
    deposito: "/movimientos/deposito",
    transferencia: "/movimientos/transferencia",
    retiro: "/movimientos/retiro",
    pago: "/movimientos/pago",
    pagoOrganizacion: "/movimientos/pago-organizacion",
    cashback: "/movimientos/cashback",
    ajusteAdmin: "/movimientos/ajuste-admin",
    reversa: (movimientoId) => `/movimientos/${movimientoId}/reversa`,
  },
  notificaciones: {
    list: "/notificaciones",
    unreadCount: "/notificaciones/no-leidas/count",
  },
  organizacion: {
    me: "/organizaciones/me",
    brandingActual: "/organizaciones/me/branding",
  },
  planes: {
    list: "/planes",
    actual: "/planes/organizacion/actual",
  },
  integraciones: {
    apiKeys: "/integraciones/api-keys",
    webhooks: "/integraciones/webhooks",
    webhookDeliveries: "/integraciones/webhooks/deliveries",
    reenviarDelivery: (deliveryId) => `/integraciones/webhooks/deliveries/${deliveryId}/reenviar`,
  },
};
